# AR planner - 3D Slicer
![image](https://user-images.githubusercontent.com/66890913/212739660-02aa4bc9-ac2a-4773-90ff-74f153838b95.png)
1. Select your CT input volume of interest (i.e. Patient001-CT_cropped.nrrd).
2. Use the image threshold slider to set up a suitable window width and window level.
3. Click on the *Create Image Slide* button to create the CT_reslice that will be sent to Unity.
4. Select the patient's spine model (i.e. P001-Spine.obj). This model should be in *Resources\Models*.
5. Import it clicking on *Load spine model*.
6. Activate the checkbox in *OpenIGTLink connection* to create an OpenIGTLink server that sends the CT_reslice.
7. Start the connection from Unity. In your HoloLens 2, you will be creating multiple screws to elaborate the planning. 3D Slicer will receive transforms associated to every screw created in HoloLens. Back in this 3D Slicer module, click on *Load screw models* anytime you want to update the screw models in the scene.
8. Use the *Save data* section to save your scene in the desired folder.
