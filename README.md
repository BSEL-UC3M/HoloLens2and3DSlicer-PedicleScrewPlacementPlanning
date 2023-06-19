# Real-Time integration between Microsoft HoloLens 2 and 3D Slicer
## Demonstration in pedicle screw placement planning

This repository has been created by Alicia Pose Díez de la Lastra, from Universidad Carlos III de Madrid. It presents a novel approach to communicate Microsoft HoloLens 2 and 3D Slicer using OpenIGTLink. This connection is applied towards pedicle screw placement planning. Here is a [video demonstration](https://www.youtube.com/watch?v=35WiSceP94Q&t=1s) of the functioning of the application. 

In this repository you will find all the necessary information and resources to run the system in your computer. We present two planning methods for the abovementioned clinical procedure:

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
   + NOTE: Before proceeding with these modules, please install extensions [SlicerIGT](https://github.com/SlicerIGT/SlicerIGT) and [OpenIGTLink](https://github.com/openigtlink/OpenIGTLink) from the Extensions Manager in 3D Slicer.
 - Unity version used: 2021.3.9f1
   + NOTE: Some of the libraries and dependencies used in this Unity project may be deprecated / non-existent in other Unity versions. Please, only use version 2021.3.9f1 to run this project.
 - For further questions, please contact apose@ing.uc3m.es

## Citation
This repository complements the paper: 

- Title: **Real-time integration between Microsoft HoloLens 2 and 3D Slicer with demonstration in pedicle screw placement planning**
- Authors: **Alicia Pose-Díez-de-la-Lastra, Tamas Ungi, David Morton, Gabor Fichtinger, and Javier Pascau.**
- Published at: **International Journal of Computer-Assisted Radiology and Surgery (IJCARS)**
- Date of publication: June 2023
- Reference: https://doi.org/10.1007/s11548-023-02977-0

If you find it useful, please consider citing us.


## Aknowledgements
 - Code: This repository borrows code from [OpenIGTLink-Unity](https://github.com/franklinwk/OpenIGTLink-Unity), [ShaderTutorials](https://github.com/ronja-tutorials/ShaderTutorials), and [IGT-UltrARsound](https://github.com/BIIG-UC3M/IGT-UltrARsound). Please, acknowledge their work if you find this repository useful!

 - Resources: The patient CT scans used in this repository were retrieved from the [VerSe database](https://github.com/anjany/verse). VerSe has resulted in numerous other publications, including the following:
   + Löffler M, Sekuboyina A, Jakob A, Grau AL, Scharr A, Husseini ME, Herbell M, Zimmer C, Baum T, Kirschke JS. A Vertebral Segmentation Dataset with Fracture Grading. Radiology: Artificial Intelligence, 2020 https://doi.org/10.1148/ryai.2020190138.
   + Liebl H, Schinz D, Sekuboyina A, ..., Kirschke JS. A computed tomography vertebral segmentation dataset with anatomical variations and multi-vendor scanner data SDATA-21-002892021. doi: 10.1038/s41597-021-01060-0 (preliminary access at https://arxiv.org/abs/2103.06360)
   + Sekuboyina A, Bayat AH, Husseini ME, Löffler M, Menze BM, ..., Kirschke JS. VerSe: A Vertebrae labelling and segmentation benchmark for multi-detector CT images. Med Image Anal. 2021 Oct;73:102166. doi: 10.1016/j.media.2021.102166. Epub 2021 Jul 22. (preliminary access at https://arxiv.org/abs/2001.09193)
