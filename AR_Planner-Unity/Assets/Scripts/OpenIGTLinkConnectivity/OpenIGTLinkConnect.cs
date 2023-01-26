// This code is based on the one provided in: https://github.com/franklinwk/OpenIGTLink-Unity
// Modified by Alicia Pose Díez de la Lastra, from Universidad Carlos III de Madrid

using UnityEngine;
using System;
using System.Net;
using System.IO;
using System.Net.Sockets;
using System.Text;
using System.Collections;
using System.Threading;
using System.Collections.Generic;
using UnityEngine.Networking;
using UnityEngine.UI;
using System.Runtime;

using Microsoft.MixedReality.Toolkit.UI;


public class OpenIGTLinkConnect : MonoBehaviour
{
    ///////// CONNECT TO 3D SLICER PARAMETERS /////////
    uint headerSize = 58; // Size of the header of every OpenIGTLink message
    private SocketHandler socketForUnityAndHoloLens; // Socket to connect to Slicer
    bool isConnected; // Boolean to check if the socket is connected
    public string ipString; // IP address of the computer running Slicer
    public int port; // Port of the computer running Slicer
    

    ///////// GENERAL VARIABLES /////////
    int scaleMultiplier = 1000; // Help variable to transform meters to millimeters and vice versa
    
       
    ///////// SEND /////////
    public List<ModelInfo> infoToSend; // Array of Models to send to Slicer
    
    /// CRC ECMA-182 to send messages to Slicer ///
    CRC64 crcGenerator;
    string CRC;
    ulong crcPolynomial;
    string crcPolynomialBinary = "0100001011110000111000011110101110101001111010100011011010010011";

    
    ///////// LISTEN /////////

    /// Image transfer information ///
    [HideInInspector] public GameObject movingPlane; // Plane to display image on
    Material mediaMaterial; // Material of the plane
    Texture2D mediaTexture; // Texture of the plane

    GameObject fixPlane; // Fix plane to display image on
    Material fixPlaneMaterial; // Material of the plane


    void Start()
    {
        // Initialize CRC Generator
        crcGenerator = new CRC64();
        crcPolynomial = Convert.ToUInt64(crcPolynomialBinary, 2);
        crcGenerator.Init(crcPolynomial);

        // Initialize texture parameters for image transfer of the moving plane
        movingPlane.transform.localScale = Vector3.Scale(transform.localScale, new Vector3(movingPlane.transform.localScale.x,-movingPlane.transform.localScale.y,movingPlane.transform.localScale.z));
        mediaMaterial = movingPlane.GetComponent<MeshRenderer>().material;
        mediaTexture = new Texture2D(512, 512, TextureFormat.Alpha8, false);
        mediaMaterial.mainTexture = mediaTexture;

        // Initialize texture parameters for image transfer of the fix plane
        fixPlane = GameObject.Find("FixedImagePlane").transform.Find("FixPlane").gameObject;
        fixPlane.transform.localScale = Vector3.Scale(transform.localScale, new Vector3(fixPlane.transform.localScale.x,-fixPlane.transform.localScale.y,fixPlane.transform.localScale.z));
        fixPlaneMaterial = fixPlane.GetComponent<MeshRenderer>().material;
        fixPlaneMaterial.mainTexture = mediaTexture;
    }

    // This function is called when the user activates the connectivity switch to start the communication with 3D Slicer
    public bool OnConnectToSlicerClick(string ipString, int port)
    {
        isConnected = ConnectToSlicer(ipString, port);
        return isConnected;
    }

    // Create a new socket handler and connect it to the server with the ip address and port provided in the function
    bool ConnectToSlicer(string ipString, int port)
    {
        socketForUnityAndHoloLens = new SocketHandler();

        Debug.Log("ipString: " + ipString);
        Debug.Log("port: " + port);
        bool isConnected = socketForUnityAndHoloLens.Connect(ipString, port);
        Debug.Log("Connected: " + isConnected);

        return isConnected;
        
    }

    // Routine that continuously sends the transform information of every model in infoToSend to 3D Slicer
    public IEnumerator SendTransformInfo()
    {
        while (true)
        {
            Debug.Log("Sending...");
            yield return null; // If you had written yield return new WaitForSeconds(1); it would have waited 1 second before executing the code below.
            // Loop foreach element in infoToSend
            foreach (ModelInfo element in infoToSend)
            {
                SendMessageToServer.SendTransformMessage(element, scaleMultiplier, crcGenerator, CRC, socketForUnityAndHoloLens);
            }
        }
    }

    // Routine that continuously listents to the incoming information from 3D Slicer. In the present code, this information could be in the form of a transform or an image message
    public IEnumerator ListenSlicerInfo()
    {
        while (true)
        {
            Debug.Log("Listening...");
            yield return null;

            ////////// READ THE HEADER OF THE INCOMING MESSAGES //////////
            byte[] iMSGbyteArray = socketForUnityAndHoloLens.Listen(headerSize);
            
            
            if (iMSGbyteArray.Length >= (int)headerSize)
            {
                ////////// READ THE HEADER OF THE INCOMING MESSAGES //////////
                // Store the information of the header in the structure iHeaderInfo
                ReadMessageFromServer.HeaderInfo iHeaderInfo = ReadMessageFromServer.ReadHeaderInfo(iMSGbyteArray);

                ////////// READ THE BODY OF THE INCOMING MESSAGES //////////
                // Get the size of the body from the header information
                uint bodySize = Convert.ToUInt32(iHeaderInfo.bodySize); 
                
                // Process the message when it is complete (that means, we have received as many bytes as the body size + the header size)
                if (iMSGbyteArray.Length >= (int)bodySize + (int)headerSize)
                {
                    // Compare different message types and act accordingly
                    if ((iHeaderInfo.msgType).Contains("TRANSFORM"))
                    {
                        // Extract the transform matrix from the message
                        Matrix4x4 matrix = ReadMessageFromServer.ExtractTransformInfo(iMSGbyteArray, movingPlane, scaleMultiplier, (int)iHeaderInfo.headerSize);
                        // Apply the transform matrix to the object
                        ApplyTransformToGameObject(matrix, movingPlane);
                    }

                    else if ((iHeaderInfo.msgType).Contains("IMAGE"))
                    {
                        // Read and apply the image content to our preview plane
                        ApplyImageInfo(iMSGbyteArray, iHeaderInfo);
                    }
                }
            }
        }
    }
    
    /// Apply transform information to GameObject ///
    void ApplyTransformToGameObject(Matrix4x4 matrix, GameObject gameObject)
    {
        Vector3 translation = matrix.GetColumn(3);
        //gameObject.transform.localPosition = new Vector3(-translation.x, translation.y, translation.z);
        //Vector3 rotation= matrix.rotation.eulerAngles;
        //gameObject.transform.localRotation = Quaternion.Euler(rotation.x, -rotation.y, -rotation.z);
        if (translation.x > 10000 || translation.y > 10000 || translation.z > 10000)
        {
            gameObject.transform.position = new Vector3(0, 0, 0.5f);
            Debug.Log("Out of limits. Default position assigned.");
        }
        else
        {
            gameObject.transform.localPosition = new Vector3(-translation.x, translation.y, translation.z);
            Vector3 rotation= matrix.rotation.eulerAngles;
            gameObject.transform.localRotation = Quaternion.Euler(rotation.x, -rotation.y, -rotation.z);
        }
    }

    //////////////////////////////// INCOMING IMAGE MESSAGE ////////////////////////////////
    void ApplyImageInfo(byte[] iMSGbyteArray, ReadMessageFromServer.HeaderInfo iHeaderInfo)
    {
        // Store the information of the image's body in the structure iImageInfo
        ReadMessageFromServer.ImageInfo iImageInfo = ReadMessageFromServer.ReadImageInfo(iMSGbyteArray, headerSize, iHeaderInfo.extHeaderSize);

        if(iImageInfo.numPixX > 0 && iImageInfo.numPixY > 0)
        {
            // Define the material and the texture of the plane that will display the image
            mediaMaterial = movingPlane.GetComponent<MeshRenderer>().material;
            mediaTexture = new Texture2D(iImageInfo.numPixX, iImageInfo.numPixY, TextureFormat.Alpha8, false);

            fixPlaneMaterial = fixPlane.GetComponent<MeshRenderer>().material;

            // Define the array that will store the image's pixels
            byte[] bodyArray_iImData = new byte[iImageInfo.numPixX * iImageInfo.numPixY];
            byte[] bodyArray_iImDataInv = new byte[bodyArray_iImData.Length];
            
            Buffer.BlockCopy(iMSGbyteArray, iImageInfo.offsetBeforeImageContent, bodyArray_iImData, 0, bodyArray_iImData.Length);

            // Invert the values of the pixels to have a dark background
            for (int i = 0; i < bodyArray_iImData.Length; i++)
            {
                bodyArray_iImDataInv[i] = (byte)(255-bodyArray_iImData[i]);
            }
            // Load the pixels into the texture and the material
            mediaTexture.LoadRawTextureData(bodyArray_iImDataInv);
            mediaTexture.Apply();
            mediaMaterial.mainTexture = mediaTexture;

            fixPlaneMaterial.mainTexture = mediaTexture;
        }
        else
        {
            //Create black texture
        }
    }
    
    // Called when the user disconnects Unity from 3D Slicer using the connectivity switch
    public void OnDisconnectClick()
    {
        socketForUnityAndHoloLens.Disconnect();
        Debug.Log("Disconnected from the server");
    }


    // Execute this function when the user exits the application
    void OnApplicationQuit()
    {
        // Release the socket.
        if (socketForUnityAndHoloLens != null)
        {
            socketForUnityAndHoloLens.Disconnect();
        }
    }
}
