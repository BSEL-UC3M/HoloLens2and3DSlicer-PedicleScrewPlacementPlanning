# Real-Time open-source integration between Microsoft HoloLens 2 and 3D Slicer
## Application for pedicle screw placement planning

This repository contains all the necessary information to replicate the experiments presented in the paper: "Real-Time open-source integration between Microsoft HoloLens 2 and 3D Slicer".
This study presents a novel approach to communicate Microsoft HoloLens 2 and 3D Slicer using OpenIGTLink.  

- aplicar la conexión a pedicle screw placement planning


This repository presents two planning methods:

 - AR method: It couples 
 - Desktop method: 

It contains four folders:

 - Resources: It contains all the resources used in the study, including the patient's information (CT scans and 3D models) and the pedicle screw models.

 - Desktop_Planner-3DSlicer: It includes the 3D Slicer module that simulates a traditional desktop planner. It is used for the "Desktop method".

 - AR_Planner-3DSlicer: It has the 3D Slicer module that complements the AR planning method. It is employed as part of the "AR method".

 - AR_Planner-Unity: It is the Unity project developed for the AR planner. It connects to 3D Slicer through OpenIGTLink to complement the AR planner. It is the second part of the "AR method".


All models required for this study are already uploaded to Resources/Models/ in both projects. In case you want to use your own models, update them all to these folders. Please, always use .obj extension for 3D model files.

## 3D Slicer modules

## Unity project




## General information
## Citation
If you fine our work helpful, please, consider citing our paper:
[...]

This repository borrows code from [*franklwin y shader*]. Please, acknowledge their work if you find this repository useful!