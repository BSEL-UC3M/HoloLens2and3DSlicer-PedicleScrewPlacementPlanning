# Real-Time open-source integration between Microsoft HoloLens 2 and 3D Slicer
## Application for pedicle screw placement planning

This repository contains all the necessary information to replicate the experiments presented in the paper: "Real-Time open-source integration between Microsoft HoloLens 2 and 3D Slicer".
The study presents a novel approach to communicate Microsoft HoloLens 2 and 3D Slicer using OpenIGTLink. This approach is then applied towards pedicle screw placement planning.


This repository presents two planning methods for the abovementioned clinical procedure:

 - AR method: It couples Microsoft HoloLens 2 to 3D Slicer using OpenIGTLink communication protocol. In the final application, a user can move a plane along a virtual 3D model of a patient’s spine and display the corresponding resliced 2D image from the CT.

<p align="center">
  <img src="https://user-images.githubusercontent.com/66890913/212952842-74105c36-9962-48a7-9aee-a0757d6b92d7.jpg" width=50%>
</p>


 - Desktop method: 2D desktop planner developed in 3D Slicer to compare with the AR application.

There are four folders in this repository:

 - *Resources*: It contains all the resources used in the study, including the patient's information (CT scans and 3D models) and the pedicle screw models.

 - *Desktop_Planner-3DSlicer*: 3D Slicer module that simulates a traditional desktop planner. It is used for the "Desktop method".

 - *AR_Planner-3DSlicer*: 3D Slicer module that complements the AR planning method. It is employed as part of the "AR method".

All models required for this study are already uploaded to Resources/Models/ in both 3D Slicer projects. In case you want to use your own models, update them all to these folders. Please, always use .obj extension for 3D model files.

 - *AR_Planner-Unity*: Unity project developed for the AR planner. It streams the AR application to Microsoft HoloLens 2 in real time. It is the second part of the "AR method".


For more information, read the README.md file within each folder.



## General information
 - 3D Slicer version used: 3D Slicer 5.0.3
 - Unity version used: 2019.3.9f1
 - For further questions, please contact apose@ing.uc3m.es

## Citation
If you fine our work helpful, please, consider citing our paper:
[...]

This repository borrows code from [OpenIGTLink-Unity](https://github.com/franklinwk/OpenIGTLink-Unity) and [ShaderTutorials](https://github.com/ronja-tutorials/ShaderTutorials). Please, acknowledge their work if you find this repository useful!
