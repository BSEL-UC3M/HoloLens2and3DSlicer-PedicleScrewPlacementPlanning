// This code was developed by Alicia Pose Díez de la Lastra, from Universidad Carlos III de Madrid
// This script creates all the functions associated to the switch buttons in the ControlPanel

// First, import some libraries of interest
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

using TMPro;

using Microsoft;
using Microsoft.MixedReality.Toolkit.Utilities;
using Microsoft.MixedReality.Toolkit.UI;
using Microsoft.MixedReality.Toolkit.Input;


using UnityEngine.UI;
using UnityEngine.EventSystems;
using System;

// Define the SwitchButtons class
public class SwitchButtons : MonoBehaviour
{
    /// OPENIGTLINK CONTROL VARIABLES ///
    string ipString; // IP address of the computer running Slicer
    int port; // Port of the computer running Slicer
    Coroutine listeningRoutine; // Coroutine to control the listening part (3D Slicer -> Unity)
    Coroutine sendingRoutine; // Coroutine to control the sending part (Unity -> 3D Slicer)
    OpenIGTLinkConnect connectToServer; // Variable that connects to the OpenIGTLinkConnect script and enables the connection between Unity and 3D Slicer
    

    /// CONNECT TO SLICER ///
    Interactable connectToSlicer_Switch; // Interactable behavior of the switch button that starts/stops the communication with 3D Slicer
    GameObject connectToSlicer_SwitchGO; // GameObject behavior of the switch button
    TextMesh connectToSlicer_label; // Label bellow the switch button that indicates if the client is correctly connected to the server

    
    /// CLIP SPINE ///
    Interactable clipSpine_Switch; // Interactable behavior of the switch button that clips the spine with the image plane
    GameObject clipSpine_SwitchGO; // GameObject behavior of the switch button
    TextMeshPro clipSpine_label; // Label bellow the switch button that indicates if the spine is clipped
    [HideInInspector] public GameObject spineModel; // GameObject corresponding to the spine model
    [HideInInspector] public Material spine_mat; // Material of the spine when it is not clipped
    [HideInInspector] public Material clipping_mat; // Material of the spine when it is clipped


    /// SPINE VISIBILITY ///
    Interactable spineVisibility_Switch; // Interactable behavior of the switch button that shows/hide the spine in the 3D view
    GameObject spineVisibility_SwitchGO; // GameObject behavior of the switch button
    TextMeshPro spineVisibility_label; // Label bellow the switch button that indicates if the spine visible
    Material visible_mat; // Material of the spine when it is visible
    Material invisible_mat; // Material of the spine when it is not visible


    /// SHOW IMAGE ///
    Interactable imageVisibility_Switch; // Interactable behavior of the switch button that shows/hide the image in the 3D view
    TextMeshPro showImage_label; // Label bellow the switch button that indicates if the image is visible
    [HideInInspector] public GameObject mobileImageGO; // GameObject of the image that can be dragged along the spine
    GameObject fixedImageGO; // GameObject of the image next to the user interface
    Interactable fixImage_Switch; // Interactable behavior of the switch button that en/unables the manipulation of the image plane in the 3D world
    TextMeshPro fixImage_label;
    [HideInInspector] public GameObject imageHandler;
    [HideInInspector] public Material imageHandlerMobile_mat;
    Material imageHandlerFixed_mat;

    


    bool isConnected;
    void Start()
    {
        /// OPENIGTLINK CONTROL VARIABLES ///
        // Get the OpenIGTLinkConnect script holder and retrieve the ip and port set in the inspector
        connectToServer = GameObject.Find("OpenIGTLinkConnectHandler").GetComponent<OpenIGTLinkConnect>();
        ipString = connectToServer.ipString; // IP address of the computer running Slicer
        port = connectToServer.port; // Port of the computer running Slicer
    

        /// CONNECT TO SLICER ///
        // Get the switch button in the hierarchy and define two functions to be executed when it is selected and when it is deselected
        connectToSlicer_Switch = GameObject.Find("ControlPanel").transform.Find("ConnectivityButtons").transform.Find("ButtonCollection").transform.Find("ConnectToSlicerButton").GetComponent<Interactable>();
        var toggleSlicerConnection = connectToSlicer_Switch.AddReceiver<InteractableOnToggleReceiver>();
        toggleSlicerConnection.OnSelect.AddListener(() => OnConnectToSlicerON(connectToSlicer_Switch));
        toggleSlicerConnection.OnDeselect.AddListener(() => OnConnectToSlicerOFF(connectToSlicer_Switch));
        
        // Change the label to Disconnected
        connectToSlicer_SwitchGO = connectToSlicer_Switch.gameObject;
        connectToSlicer_label = GameObject.Find("disConnectedLabel").GetComponent<TextMesh>();
        connectToSlicer_label.text = "Disconnected \nfrom Slicer";

        
        /// CLIP SPINE ///
        // Get the switch button in the hierarchy and define two functions to be executed when it is selected and when it is deselected
        clipSpine_Switch = GameObject.Find("ControlPanel").transform.Find("ImageButtons").transform.Find("ButtonCollection").transform.Find("ClipSpineSwitch").GetComponent<Interactable>();
        var toggleClipSpine = clipSpine_Switch.AddReceiver<InteractableOnToggleReceiver>();
        toggleClipSpine.OnSelect.AddListener(() => OnClipSpineON(clipSpine_Switch));
        toggleClipSpine.OnDeselect.AddListener(() => OnClipSpineOFF(clipSpine_Switch));

        clipSpine_SwitchGO = clipSpine_Switch.gameObject;
        // Change the label to OFF and deactivate the button. This button will only be enabled while the client is connected to the server
        clipSpine_label = GameObject.Find("ClipSpineLabel").GetComponent<TextMeshPro>();
        clipSpine_label.text = "Clip spine OFF";
        clipSpine_Switch.IsToggled = false;
        clipSpine_Switch.IsEnabled = false;


        /// SPINE VISIBILITY ///
        // Get the switch button in the hierarchy and define two functions to be executed when it is selected and when it is deselected
        spineVisibility_Switch = GameObject.Find("ControlPanel").transform.Find("SpineButtons").transform.Find("ButtonCollection").transform.Find("SpineVisibilitySwitch").GetComponent<Interactable>();
        var toggleSpineVisibility = spineVisibility_Switch.AddReceiver<InteractableOnToggleReceiver>();
        toggleSpineVisibility.OnSelect.AddListener(() => OnTurnModelON(spineVisibility_Switch));
        toggleSpineVisibility.OnDeselect.AddListener(() => OnTurnModelOFF(spineVisibility_Switch));
        
        spineVisibility_SwitchGO = spineVisibility_Switch.gameObject;
        // Change the label to ON (the spine is visible)
        spineVisibility_label = GameObject.Find("ShowSpineLabel").GetComponent<TextMeshPro>();
        spineVisibility_label.text = "Spine ON";
        // Load the invisible material from the path
        invisible_mat = Resources.Load("Materials/Invisible_mat") as Material;
        

        /// SHOW IMAGE ///
        // Get the switch button in the hierarchy and define two functions to be executed when it is selected and when it is deselected
        imageVisibility_Switch = GameObject.Find("ControlPanel").transform.Find("ImageButtons").transform.Find("ButtonCollection").transform.Find("ImageVisibilitySwitch").GetComponent<Interactable>();
        var toggleShowImage = imageVisibility_Switch.AddReceiver<InteractableOnToggleReceiver>();
        toggleShowImage.OnSelect.AddListener(() => OnShowImageON(imageVisibility_Switch));
        toggleShowImage.OnDeselect.AddListener(() => OnShowImageOFF(imageVisibility_Switch));

        showImage_label = GameObject.Find("ShowImageLabel").GetComponent<TextMeshPro>();
        // Change the label to OFF and deactivate the button. This button will only be enabled while the client is connected to the server
        showImage_label.text = "Image OFF";
        imageVisibility_Switch.IsEnabled = false;
        imageVisibility_Switch.IsToggled = false;

        /// FIX IMAGE ///
        // Initialize image handler colors
        imageHandlerFixed_mat = Resources.Load("Materials/ImageFixed_mat") as Material; // Load the fixed image material
        // Get the switch button in the hierarchy and define two functions to be executed when it is selected and when it is deselected
        fixImage_Switch = GameObject.Find("ControlPanel").transform.Find("ImageButtons").transform.Find("ButtonCollection").transform.Find("FixImageSwitch").GetComponent<Interactable>();
        var toggleFixImage = fixImage_Switch.AddReceiver<InteractableOnToggleReceiver>();
        PressableButtons manageModelsScript = GameObject.Find("Models").GetComponent<PressableButtons>();
        toggleFixImage.OnSelect.AddListener(() => OnFixImageON(fixImage_Switch, mobileImageGO, manageModelsScript, imageHandler, imageHandlerFixed_mat));
        toggleFixImage.OnDeselect.AddListener(() => OnFixImageOFF(fixImage_Switch, mobileImageGO, manageModelsScript, imageHandler, imageHandlerMobile_mat));

        

        fixedImageGO = GameObject.Find("ControlPanel").transform.Find("FixedImagePlane").gameObject;
        // Change the label to OFF and deactivate the button. This button will only be enabled while the client is connected to the server
        fixImage_label = GameObject.Find("FixImageLabel").GetComponent<TextMeshPro>();
        fixImage_label.text = "Fix image OFF";
        fixImage_Switch.IsEnabled = false;
        fixImage_Switch.IsToggled = false;
        
    }

    /// CONNECT TO SLICER ///
    // This function is called everytime the user activates the connectivity switch
    void OnConnectToSlicerON(Microsoft.MixedReality.Toolkit.UI.Interactable toggleSwitch)
    {
        // Start the connection with Slicer
        isConnected = connectToServer.OnConnectToSlicerClick(ipString, port);
        // If the connection is successful, continue
        if (isConnected)
        {
            // Change the label to "Connected", enable the rest of the switches in the UI and start the listening and sending coroutines
            connectToSlicer_label.text = "Connected \nto Slicer";
            clipSpine_Switch.IsEnabled = true;
            fixImage_Switch.IsEnabled = true;
            imageVisibility_Switch.IsEnabled = true;
            imageVisibility_Switch.IsToggled = true;
            listeningRoutine = StartCoroutine(connectToServer.ListenSlicerInfo());
            sendingRoutine = StartCoroutine(connectToServer.SendTransformInfo());
            mobileImageGO.SetActive(true);
        }
        // If the connection is unsuccesful, keep things as they were
        else
        {
            connectToSlicer_label.text = "Disconnected \nfrom Slicer";
            toggleSwitch.IsToggled = false;
        }
    }

    // This function is called everytime the user deactivates the connectivity switch
    void OnConnectToSlicerOFF(Microsoft.MixedReality.Toolkit.UI.Interactable toggleSwitch)
    {
        // If there are any listening or sending coroutines active, stop them
        try
        {
            StopCoroutine(listeningRoutine);
        }
        catch { }
        try
        {
            StopCoroutine(sendingRoutine);
        }
        catch { }
        // Disconnect from the server
        connectToServer.OnDisconnectClick();
        // Change the label to "Disconnected"        
        connectToSlicer_label.text = "Disconnected \nfrom Slicer";
        // Unable the rest of switch buttons in the UI
        clipSpine_Switch.IsEnabled = false;
        imageVisibility_Switch.IsEnabled = false;
        fixImage_Switch.IsEnabled = false;
    }

    
    /// CLIP SPINE ///
    // This function is called everytime the user activates the clipping tool
    void OnClipSpineON(Microsoft.MixedReality.Toolkit.UI.Interactable index)
    {
        // Assign the clipping material to the spine. This material is already associated to the image plane, by definition
        spineModel.GetComponentInChildren<MeshRenderer>().material = clipping_mat;
        clipSpine_label.text = "Clip spine ON";
    }
    // This function is called everytime the user deactivates the clipping tool
    void OnClipSpineOFF(Microsoft.MixedReality.Toolkit.UI.Interactable index)
    {
        // Assign the spine material to the spine (no clipping)
        spineModel.GetComponentInChildren<MeshRenderer>().material = spine_mat;
        clipSpine_label.text = "Clip spine OFF";
    }

    /// SPINE VISIBILITY ///
    // This function is called everytime the user activates the spine visibility switch button
    void OnTurnModelON(Microsoft.MixedReality.Toolkit.UI.Interactable index)
    {
        // Assign the visible material to the spine
        spineModel.GetComponentInChildren<MeshRenderer>().material = visible_mat;
        // Update the button label
        spineVisibility_label.text = "Spine ON";
    }

    // This function is called everytime the user deactivates the spine visibility switch button
    void OnTurnModelOFF(Microsoft.MixedReality.Toolkit.UI.Interactable index)
    {
        // Assign the non-visible material to the spine
        visible_mat = spineModel.GetComponentInChildren<MeshRenderer>().material; // the visible material could be spine_mat or clipping_mat
        spineModel.GetComponentInChildren<MeshRenderer>().material = invisible_mat;
        // Update the button label
        spineVisibility_label.text = "Spine OFF";
    }

    /// SHOW IMAGE ///
    // This function is called everytime the user activates the image visibility switch button
    void OnShowImageON(Microsoft.MixedReality.Toolkit.UI.Interactable index)
    {
        // Set the both images visibilities to true
        mobileImageGO.SetActive(true);
        fixedImageGO.SetActive(true);
        // Start the listening coroutine
        listeningRoutine = StartCoroutine(connectToServer.ListenSlicerInfo());
        // Enable the other switch buttons
        clipSpine_Switch.IsEnabled = true;
        fixImage_Switch.IsEnabled = true;
        // Update the label
        showImage_label.text = "Image ON";
    }

    // This function is called everytime the user deactivates the image visibility switch button
    void OnShowImageOFF(Microsoft.MixedReality.Toolkit.UI.Interactable index)//, string toggleSwitchText)
    {
        // Set the both images visibilities to false
        mobileImageGO.SetActive(false);
        fixedImageGO.SetActive(false);
        // If the listening routine was running, stop it
        try{
            StopCoroutine(listeningRoutine);
        }
        catch { }
        // Since we don't see the image anymore, also stop the clipping of the spine
        OnClipSpineOFF(clipSpine_Switch);
        // Unable all the buttons associated to the image plane
        clipSpine_Switch.IsEnabled = false;
        clipSpine_Switch.IsToggled = false;
        fixImage_Switch.IsEnabled = false;
        fixImage_Switch.IsEnabled = false;
        // Update the show image label
        showImage_label.text = "Image OFF";
        // Assign the spine_mat to the spine (in case it has the clipping mat)
        spineModel.GetComponentInChildren<MeshRenderer>().material = spine_mat;
    }

    // This function is called everytime the user fixes the image plane in the 3D world using the corresponging switch button
    void OnFixImageON(Microsoft.MixedReality.Toolkit.UI.Interactable index, GameObject mobileImageGO, PressableButtons manageModelsScript, GameObject imageHandler, Material imageHandlerFixed_mat)
    {
        // Make the object non-manipulable
        manageModelsScript.MakeObjectManipulable(mobileImageGO, false);
        // Change the color of the image handler accordingly
        imageHandler.GetComponent<MeshRenderer>().material = imageHandlerFixed_mat;
        // Update the button label
        fixImage_label.text = "Fix image ON";
    }

    void OnFixImageOFF(Microsoft.MixedReality.Toolkit.UI.Interactable index, GameObject mobileImageGO, PressableButtons manageModelsScript, GameObject imageHandler, Material imageHandlerMobile_mat)
    {
        // Make the object manipulable
        manageModelsScript.MakeObjectManipulable(mobileImageGO, true);
        // Change the color of the image handler accordingly
        imageHandler.GetComponent<MeshRenderer>().material = imageHandlerMobile_mat;
        // Update the button label
        fixImage_label.text = "Fix image OFF";
    }
    
}


