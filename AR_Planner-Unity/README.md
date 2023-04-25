# AR Planner - Unity
## Prerequisites and setting up the project
 1. Download this project and open it in Unity (version 2021.3.9f1).
 2. Set up the project configuration with MRTK following the steps in [this tutorial](https://learn.microsoft.com/es-es/training/modules/learn-mrtk-tutorials/1-5-exercise-configure-resources?tabs=openxr).
 3. Open the scene *PedicleScrews*.
 4. In the Hierarchy, click on *OpenIGTLinkConnectHandler* to find the *OpenIGTLinkConnect* script. Specify the IP string and port of your OpenIGTLink server from 3D Slicer. If 3D Slicer is running on the same computer as Unity, you can write *localhost*.
 5. In the Hierarchy, click on *Models* to find the *PressableButtons* script. Specify the Patient Number.
 6. In the top menu, click on *Mixed Reality > Remoting > Holographic Remoting for Play Mode* to enable the [Holographic Remoting connection](https://learn.microsoft.com/en-us/windows/mixed-reality/develop/native/holographic-remoting-player).
 7. Find your Microsoft HoloLens 2 IP address within the Holographic Remoting Player app and write it in the *Remote Host Name* section.
 8. Click on *Enable Holographic Remoting for Play Mode*. Make sure your HoloLens 2 and your computer are connected to the same WiFi.
 9. Click on the Play button to run the Editor mode.
 10. Whenever Unity finds your HoloLens 2, it will start streaming the app.



## Microsoft HoloLens 2 app
![20221213_161218_HoloLens](https://user-images.githubusercontent.com/66890913/212738384-b34e4456-db0d-4aae-bdd6-63f0c58c9275.jpg)
The application starts with the 3D model of the spine corresponding to the patient of interest (with coordinates [0,0,0.5]), and a control panel. The user can perform intuitive gestures to grab all the holograms and move and rotate them in their world. The control panel contains several buttons classified in four categories:
-	Connectivity: Start or stop the communication with 3D Slicer.
-	Spine: Turn on / off spine visibility and en/disable the manipulation of the spine in the 3D world.
-	Image: Turn on / off image visibility, use it to clip the spine model, or en/disable the image model manipulation in the 3D world. The clipping tool was designed to clip the spine model with the CT reslice panel.
-	Screws: Create a new screw, delete it, en/disable its manipulation in the 3D world, and change its thickness and length. The "next" button iterates over all the screws in the scene to select the one of interest for the modifications.
-	CT slide: Duplicate of the CT image slide of the patient.


## Unity editor - Hierarchy elements
 ![image](https://user-images.githubusercontent.com/66890913/212734351-518aab0c-b91a-4ec1-91a5-2a45e1f5f2c7.png)
- OpenIGTLinkConnectHandler: Contains the *OpenIGTLinkConnect* script. It is used to create an OpenIGTLink client in Unity and find the OpenIGTLink server in 3D Slicer. It also displays all the transform elements that will be sent to 3D Slicer (InfoToSend array).
- Models: It contains all the 3D models of the scene (including the spine, the CT image reslice and all the pedicle screws). When the application is not running, this element does not contain any children. All the 3D models will appear as children when the app enters in play mode. This element contains the *ModelScaling* and the *PressableButtons* scripts. The second one is the main script of the project. Select here the patient number: 1 for P001-Spine, 2 for P002-Spine
- ControlPanel: It is the user interface to manipulate the 3D models from the AR glasses. It contains the *SwitchButtons* script that controls the functions of the switch buttons of the panel. The pressable buttons' functions are controlled with the *PressableButtons* script within *Models*.
- Canvas: These are 3 buttons to reset the scene, save it and load it back. These buttons are not visible from the AR device. They can just be accessed from the Unity Editor.

## Load your own models
Models are currently loaded from the "PressableButtons.cs" script. You can find it in "Assets > Scripts > ControlPanel > PressableButtons.cs".
On the Start() function you define the route to your models (for instance, the path towards the Spine prefab is defined in line 66 as spineModelPath). Then, you load the model using the functions Resources.Load() and GameObject.Instantiate(). 
You could load your own models on Start by copying and pasting this same code as often as you want with the name of your prefabs (lines 64-71).
To create your prefabs follow:
     1. Load any OBJ file into a "Models" folder in your assets folder (Unity can't interpret STL files).
     2. Manually drag and drop it to your Hierarchy window to instantiate them in the scene. If you are importing a model from 3D Slicer you may have to scale it by 0.001 to convert the default units from Slicer (millimeters) to the default units in Unity (meters)
     3. Attach to them the following scripts: a collider, "NearInteractionGrabbable", "Object Manipulator (Script)", "Constraint Manager (Script)" and "Model Info (Script)". 
     4. Drag and drop back your GameObject into a "Prefabs" folder
With this, you define a prefab that can be easily loaded following the instructions above and that will be manipulable with your hand so that you can translate and rotate it in the 3D world. Thanks to the Model Info script, you can also send its information to 3D Slicer using the protocol defined in this work.


