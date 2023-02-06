# This code has been developed by Alicia Pose Díez de la Lastra (Universidad Carlos III de Madrid) and David Morton (PerkLab)
# It is based on the template designed by Jean-Christophe Fillion-Robin (Kitware Inc.), Andras Lasso (PerkLab), and Steve Pieper (Isomics, Inc).
import logging
import os

import vtk

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

import numpy as np
import time
from pathlib import Path

#
# AR_Planner
#

class AR_Planner(ScriptedLoadableModule):
	"""Uses ScriptedLoadableModule base class, available at:
	https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
	"""

	def __init__(self, parent):
			ScriptedLoadableModule.__init__(self, parent)
			self.parent.title = "AR_Planner"
			self.parent.categories = ["PedicleScrewPlacementPlanner"]
			self.parent.contributors = ["Alicia Pose (Universidad Carlos III de Madrid) and David Morton (Queen's University)"]
	"""
	This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
	and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
	"""
	


#
# AR_PlannerWidget
#

class AR_PlannerWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
	"""Uses ScriptedLoadableModuleWidget base class, available at:
	https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
	"""

	def __init__(self, parent=None):
		"""
		Called when the user opens the module the first time and the widget is initialized.
		"""
		ScriptedLoadableModuleWidget.__init__(self, parent)
		VTKObservationMixin.__init__(self)  # needed for parameter node observation
		self.logic = None
		self._parameterNode = None
		self._updatingGUIFromParameterNode = False

	def setup(self):
		"""
		Called when the user opens the module the first time and the widget is initialized.
		"""
		ScriptedLoadableModuleWidget.setup(self)

		# Load widget from .ui file (created by Qt Designer).
		# Additional widgets can be instantiated manually and added to self.layout.
		uiWidget = slicer.util.loadUI(self.resourcePath('UI/AR_Planner.ui'))
		self.layout.addWidget(uiWidget)
		self.ui = slicer.util.childWidgetVariables(uiWidget)

		# Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
		# "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
		# "setMRMLScene(vtkMRMLScene*)" slot.
		uiWidget.setMRMLScene(slicer.mrmlScene)

		# Create logic class. Logic implements all computations that should be possible to run
		# in batch mode, without a graphical user interface.
		self.logic = AR_PlannerLogic()

		# Connections

		# These connections ensure that we update parameter node when scene is closed
		self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
		self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)
					
		# These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
		# (in the selected parameter node).

		### INPUTS SECTION

		self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onInputVolumeUpdated)
		self.ui.inputVolumePath.connect("currentPathChanged(QString)", self.onInputVolumePathUpdated)
		self.ui.loadInputVolumeButton.connect("clicked(bool)", self.onLoadInputVolumeClicked)

		self.ui.imageWWSpinBox.connect("valueChanged(double)", self.onWWSpinBoxChanged)
		self.ui.imageHistogramSlideBar.connect("valuesChanged(double,double)", self.onImageHistogramSlideBarChanged)
		self.ui.imageWLSpinBox.connect("valueChanged(double)", self.onWLSpinBoxChanged)
		self.ui.createImageSliceButton.connect('clicked(bool)', self.onCreateImageSliceClicked)

		self.ui.modelsPath.connect("currentPathChanged(QString)", self.onModelsPathUpdated)
		self.ui.loadSpineModelButton.connect('clicked(bool)', self.onLoadSpineModelFromFileClicked)

        #### OpenIGTLink Connection SECTION
		self.ui.serverActiveCheckBox.connect("toggled(bool)", self.onActivateOpenIGTLinkConnectionClicked)

		### Update screws SECTION
		self.ui.screwDirButton.connect('directorySelected(QString)', self.onScrewDirChanged)
		self.ui.loadScrewModelsButton.connect('clicked(bool)', self.onLoadScrewModelsFromFileClicked)

		### SAVE SECTION
		self.ui.savingPath.connect('directorySelected(QString)', self.onSaveDirectoryChanged)
		self.ui.patientID_text.connect("textChanged(QString)", self.updateParameterNodeFromGUI)
		self.ui.userID_text.connect("textChanged(QString)", self.updateParameterNodeFromGUI)
		self.ui.saveDataButton.connect('clicked(bool)', self.onSaveDataClicked)

		# Make sure parameter node is initialized (needed for module reload)
		self.initializeParameterNode()
		self.initializeGUI() # This is an addition to avoid initializing parameter node before connections

	def initializeGUI(self):
		"""
			initailize the save directory using settings
		"""
		settings = slicer.app.userSettings()
		if settings.value(self.logic.SAVING_DIRECTORY): # if the settings exists
			self.ui.savingPath.directory = settings.value(self.logic.SAVING_DIRECTORY)
		if settings.value(self.logic.INPUT_VOLUME_PATH):
			self.ui.inputVolumePath.setCurrentPath(settings.value(self.logic.INPUT_VOLUME_PATH))
		if settings.value(self.logic.MODELS_DIRECTORY):
			self.ui.modelsPath.setCurrentPath(settings.value(self.logic.MODELS_DIRECTORY))
		if settings.value(self.logic.SCREWS_DIRECTORY):
			self.ui.screwDirButton.directory = settings.value(self.logic.SCREWS_DIRECTORY)


	def cleanup(self):
		"""
		Called when the application closes and the module widget is destroyed.
		"""
		self.removeObservers()

	def enter(self):
		"""
		Called each time the user opens this module.
		"""
		# Make sure parameter node exists and observed
		self.initializeParameterNode()

	def exit(self):
		"""
		Called each time the user opens a different module.
		"""
		# Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
		self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

	def onSceneStartClose(self, caller, event):
		"""
		Called just before the scene is closed.
		"""
		# Parameter node will be reset, do not use it anymore
		self.setParameterNode(None)

	def onSceneEndClose(self, caller, event):
		"""
		Called just after the scene is closed.
		"""
		# If this module is shown while the scene is closed then recreate a new parameter node immediately
		if self.parent.isEntered:
				self.initializeParameterNode()

	#
	# UI functions
	#

	def onInputVolumePathUpdated(self, path):
		'''
		Updates the input volume path in the settings
		'''
		settings = slicer.app.userSettings()
		settings.setValue(self.logic.INPUT_VOLUME_PATH, path)
		# enable the button	
		self.ui.loadInputVolumeButton.enabled = True

	def onLoadInputVolumeClicked(self):
		'''
		Loads the input volume from the path
		'''
		# Get the path from the GUI
		path = self.ui.inputVolumePath.currentPath
		# Get the volume name from the path
		filename = os.path.splitext(os.path.basename(path))[0]
		# Load the volume
		volumeNode = slicer.util.loadVolume(path)
		# Set the volume as the input volume
		self.ui.inputSelector.setCurrentNode(volumeNode)
		# disable the button
		self.ui.loadInputVolumeButton.enabled = False

	def onInputVolumeUpdated(self):
		"""
		This method is called when the input volume is changed.
		It updates the range of the histogram slide bar, and the WW and WL spin boxes.
		"""
		self.updateParameterNodeFromGUI()
		self.logic.updateHistLimitsFromInput()
		# Update the slide bar limits
		self.ui.imageHistogramSlideBar.minimum = float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_minLimit))
		self.ui.imageHistogramSlideBar.maximum = float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_maxLimit))
		# Set the maximum and minimum values for the WW and WL spin boxes
		maxWidth = float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_maxLimit)) - float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_minLimit))
		self.ui.imageWWSpinBox.minimum = 0.0
		self.ui.imageWWSpinBox.maximum = maxWidth
		minLevel = float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_minLimit))
		maxLevel = float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_maxLimit))
		self.ui.imageWLSpinBox.maximum = maxLevel
		self.ui.imageWLSpinBox.minimum = minLevel
		# update the window level to be zero and the width to be half the maximum in the parameter node
		self._parameterNode.SetParameter(self.logic.WINDOW_LEVEL, str(0))
		self._parameterNode.SetParameter(self.logic.WINDOW_WIDTH, str(0.5*maxWidth))

	def onWWSpinBoxChanged(self, value):
		"""
		Updates the Window Width value in the parameter node
		"""
		parameterNode = self.logic.getParameterNode()
		parameterNode.SetParameter(self.logic.WINDOW_WIDTH, str(value))
		self.updateGUIFromParameterNode()
		self.logic.UpdateImageValuesWithSlider()

	def onWLSpinBoxChanged(self, value):
		"""
		Updates the Window Level value in the parameter node
		"""
		parameterNode = self.logic.getParameterNode()
		parameterNode.SetParameter(self.logic.WINDOW_LEVEL, str(value))
		self.updateGUIFromParameterNode()
		self.logic.UpdateImageValuesWithSlider()

	def onImageHistogramSlideBarChanged(self):
		"""
		Updates the Window Width and Window Level values in the parameter node
		"""
		parameterNode = self.logic.getParameterNode()
		parameterNode.SetParameter(self.logic.WINDOW_WIDTH, str(self.ui.imageHistogramSlideBar.maximumValue - self.ui.imageHistogramSlideBar.minimumValue))
		parameterNode.SetParameter(self.logic.WINDOW_LEVEL, str((self.ui.imageHistogramSlideBar.maximumValue + self.ui.imageHistogramSlideBar.minimumValue)/2))
		self.updateGUIFromParameterNode()
		self.logic.UpdateImageValuesWithSlider()

	def onCreateImageSliceClicked(self):
		"""
		Run processing when user clicks "Create Image Slide" button.
		"""
		self.updateParameterNodeFromGUI()
		with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):
			# Compute output
			self.logic.CreateImageSlice()
			# disable the button
			self.ui.createImageSliceButton.enabled = False

	def onModelsPathUpdated(self, path):
		'''
		Updates the models path in the settings
		'''
		settings = slicer.app.userSettings()
		settings.setValue(self.logic.MODELS_DIRECTORY, path)
		# enable the button	
		self.ui.loadSpineModelButton.enabled = True

	def onLoadSpineModelFromFileClicked(self):
		"""
		Run processing when user clicks "Load Models" button.
		"""
		self.updateParameterNodeFromGUI()
		with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):
			parameterNode = self.logic.getParameterNode()
			# Load spine model and change its color
			spineFileName = parameterNode.GetParameter(self.logic.SPINE_FILENAME)
			spinePath = parameterNode.GetParameter(self.logic.MODELS_DIRECTORY) # Get path to screw models
			boneColor = np.array([241,214,145])/255
			spineModel = self.logic.LoadModelFromFile(spinePath, spineFileName, boneColor, True)
			self._parameterNode.SetNodeReferenceID(self.logic.SPINE_MODEL, spineModel.GetID()) ## Update parameter node
			
			# Build transform tree       
			spineTransformName = "Spine_T"
			spineTransform = self.logic.ApplyTransformToObject(spineModel, spineTransformName)
			self._parameterNode.SetNodeReferenceID(self.logic.SPINE_TRANSFORM, spineTransform.GetID()) ## Update parameter node

			imageTransform = slicer.util.getFirstNodeByName("Image_T")
			self.logic.ApplyTransformToObject(imageTransform, spineTransformName)

			# set the spine model as the current model
			self.ui.loadSpineModelButton.enabled = False

	def onScrewDirChanged(self, path):
		'''
		Updates the screw models path in the settings
		'''
		settings = slicer.app.userSettings()
		settings.setValue(self.logic.SCREWS_DIRECTORY, path)
		

	def onLoadScrewModelsFromFileClicked(self):
		"""
		Run processing when user clicks "Load screw models" button.
		"""
		self.updateParameterNodeFromGUI()
		self.logic.LoadScrewModelsFromFile()

	def onActivateOpenIGTLinkConnectionClicked(self, connect):
		"""
		Run processing when user clicks on the OpenIGTLink checkbox.
		"""
		self.updateParameterNodeFromGUI()
		# Update connection 
		if connect: # If the connection (checkbox) is enabled
				port_tracker = 18944
				status = self.logic.StartOIGTLConnection(port_tracker) # Start connection
				if status == 1:
						self.connect = False # set connect variable to false
						self.ui.OIGTLconnectionLabel.text = "OpenIGTLink server - ACTIVE" # Update displaying text
		else: # If the connection (checkbox) is enabled
				self.logic.StopOIGTLConnection() # Stop connection
				self.connect = True # set connect variable to true
				self.ui.OIGTLconnectionLabel.text = "OpenIGTLink server - INACTIVE" # Update displaying text
				
	def onSaveDirectoryChanged(self, directory):
		"""
		Run processing when user selects a new saving location.
		"""
		# update settings with the new directory
		settings = slicer.app.userSettings()
		settings.setValue(self.logic.SAVING_DIRECTORY, directory)

	def onSaveDataClicked(self):
		"""
		Run processing when user clicks "Save Data" button.
		"""
		self.updateParameterNodeFromGUI()
		with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

				# Compute output
				save_folder_path = self.logic.SaveData()
				self.ui.filesSavedLabel.setText("All files have been saved in:\n" + save_folder_path)

	#
	# Parameter node and GUI interaction
	# 			             
	def initializeParameterNode(self):
		"""
		Ensure parameter node exists and observed.
		"""
		# Parameter node stores all user choices in parameter values, node selections, etc.
		# so that when the scene is saved and reloaded, these settings are restored.

		self.setParameterNode(self.logic.getParameterNode())

		# Select default input nodes if nothing is selected yet to save a few clicks for the user
		if not self._parameterNode.GetNodeReference(self.logic.INPUT_VOLUME):
				firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
				if firstVolumeNode:
						self._parameterNode.SetNodeReferenceID(self.logic.INPUT_VOLUME, firstVolumeNode.GetID())

		if not self._parameterNode.GetNodeReference(self.logic.WINDOW_WIDTH):
						self._parameterNode.SetNodeReferenceID(self.logic.WINDOW_WIDTH, "1000")                

		if not self._parameterNode.GetNodeReference(self.logic.WINDOW_LEVEL):
						self._parameterNode.SetNodeReferenceID(self.logic.WINDOW_LEVEL, "0")  

		if not self._parameterNode.GetNodeReference(self.logic.IMAGE_HIST_SLIDEBAR_minLimit):
				self._parameterNode.SetParameter(self.logic.IMAGE_HIST_SLIDEBAR_minLimit, "500")

		if not self._parameterNode.GetNodeReference(self.logic.IMAGE_HIST_SLIDEBAR_maxLimit):
				self._parameterNode.SetParameter(self.logic.IMAGE_HIST_SLIDEBAR_maxLimit, "1500")

		if not self._parameterNode.GetNodeReference(self.logic.MODELS_DIRECTORY):
				modelsPath = os.path.join(os.path.dirname(__file__), 'Resources/Models')
				self._parameterNode.SetParameter(self.logic.MODELS_DIRECTORY, modelsPath)

	def setParameterNode(self, inputParameterNode):
		"""
		Set and observe parameter node.
		Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
		"""

		if inputParameterNode:
				self.logic.setDefaultParameters(inputParameterNode)

		# Unobserve previously selected parameter node and add an observer to the newly selected.
		# Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
		# those are reflected immediately in the GUI.
		if self._parameterNode is not None:
				self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
		self._parameterNode = inputParameterNode
		if self._parameterNode is not None:
				self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

		# Initial GUI update
		self.updateGUIFromParameterNode()

	def updateGUIFromParameterNode(self, caller=None, event=None):
		"""
		This method is called whenever parameter node is changed.
		The module GUI is updated to show the current state of the parameter node.
		"""

		if self._parameterNode is None or self._updatingGUIFromParameterNode:
				return

		# Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
		self._updatingGUIFromParameterNode = True

		# Update node selectors and sliders
		self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference(self.logic.INPUT_VOLUME))
		
		# if the window level and width are set
		if self._parameterNode.GetParameter(self.logic.WINDOW_LEVEL) and self._parameterNode.GetParameter(self.logic.WINDOW_WIDTH):
			# update the WW and WL spin boxes
			WL = float(self._parameterNode.GetParameter(self.logic.WINDOW_LEVEL))
			WW = float(self._parameterNode.GetParameter(self.logic.WINDOW_WIDTH))
			self.ui.imageWWSpinBox.value = WW
			self.ui.imageWLSpinBox.value = WL
			# Update the histogram slide bar
			minVAL = WL - WW/2
			maxVAL = WL + WW/2
			self.ui.imageHistogramSlideBar.minimumValue = minVAL
			self.ui.imageHistogramSlideBar.maximumValue = maxVAL

		# Update buttons states and tooltips
		if self._parameterNode.GetNodeReference("InputVolume"):
				self.ui.createImageSliceButton.toolTip = "Compute output volume"
				self.ui.createImageSliceButton.enabled = True
		else:
				self.ui.createImageSliceButton.toolTip = "Select input volume nodes"
				self.ui.createImageSliceButton.enabled = False

		if (self._parameterNode.GetParameter(self.logic.PATIENT_ID)=='') | (self._parameterNode.GetParameter(self.logic.USER_ID)==''):
				self.ui.saveDataButton.toolTip = "Set patient and user IDs"
				self.ui.saveDataButton.enabled = False
		else:
				self.ui.saveDataButton.toolTip = "Save data"
				self.ui.saveDataButton.enabled = True
			
		# All the GUI updates are done
		self._updatingGUIFromParameterNode = False

	def updateParameterNodeFromGUI(self, caller=None, event=None):
		"""
		This method is called when the user makes any change in the GUI.
		The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
		"""

		if self._parameterNode is None or self._updatingGUIFromParameterNode:
				return

		wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

		self._parameterNode.SetNodeReferenceID(self.logic.INPUT_VOLUME, self.ui.inputSelector.currentNodeID)

		self._parameterNode.SetParameter(self.logic.ACTIVE_SERVER_CHECKBOX, "true" if self.ui.serverActiveCheckBox.checked else "false")
		self._parameterNode.SetParameter(self.logic.PATIENT_ID, (self.ui.patientID_text).text)
		self._parameterNode.SetParameter(self.logic.USER_ID, (self.ui.userID_text).text)
		(spineDirName, spineFileName) = os.path.split(self.ui.modelsPath.currentPath)
		self._parameterNode.SetParameter(self.logic.MODELS_DIRECTORY, spineDirName)
		self._parameterNode.SetParameter(self.logic.SPINE_FILENAME, spineFileName)
		self._parameterNode.SetParameter(self.logic.SCREWS_DIRECTORY, self.ui.screwDirButton.directory)
		
		
		self._parameterNode.EndModify(wasModified)


#
# AR_PlannerLogic
#

class AR_PlannerLogic(ScriptedLoadableModuleLogic, VTKObservationMixin):

	# Image slide
	INPUT_VOLUME = 'InputVolume'
	INPUT_VOLUME_PATH = 'InputPath'

	IMAGE_HIST_SLIDEBAR_minLimit = 'ImageHistogramSlideBar_minLimit'
	IMAGE_HIST_SLIDEBAR_maxLimit = 'ImageHistogramSlideBar_maxLimit'
	WINDOW_WIDTH = 'WindowWidth'
	WINDOW_LEVEL = 'WindowLevel'

	# OpenIGTLink connection
	ACTIVE_SERVER_CHECKBOX = 'serverActiveCheckBox'

	# Models
	MODELS_DIRECTORY = 'ModelsDirectory'
	SPINE_MODEL = 'SpineModel'
	SPINE_FILENAME = 'SpineFileName'
	SCREWS_DIRECTORY = 'ScrewsDirectory'

	# Transforms
	SPINE_TRANSFORM = 'Spine_T'
	IMAGE_TRANSFORM = 'Image_T'

	# Saving path
	SAVING_DIRECTORY = 'savingPath'
	PATIENT_ID = 'PatientID'
	USER_ID = 'UserID'

	# Parameters
	CT_RESLICE_OUTPUT = 'CT_reslice'

	def __init__(self):
		"""
		Called when the logic class is instantiated. Can be used for initializing member variables.
		"""
		ScriptedLoadableModuleLogic.__init__(self)

	def setDefaultParameters(self, parameterNode):
		"""
		Initialize parameter node with default settings.
		"""
		if not parameterNode.GetParameter(self.ACTIVE_SERVER_CHECKBOX):
				parameterNode.SetParameter(self.ACTIVE_SERVER_CHECKBOX, "0")

	def updateHistLimitsFromInput(self):
		"""
		Update the min and max values of the histogram slide bar from the input volume.
		"""
		parameterNode = self.getParameterNode()
		inputVolume = parameterNode.GetNodeReference(self.INPUT_VOLUME)
		# if the volume is not loaded, set the hist slidebar to 
		if inputVolume is None:
			return
		# get the image array
		imageArray = slicer.util.arrayFromVolume(inputVolume)
		# get the min and max values of the image array
		minValue = int(imageArray.min())
		maxValue = int(imageArray.max())
		# set the min and max values in the parameter node
		parameterNode.SetParameter(self.IMAGE_HIST_SLIDEBAR_minLimit, str(minValue))
		parameterNode.SetParameter(self.IMAGE_HIST_SLIDEBAR_maxLimit, str(maxValue))			

	def UpdateImageValuesWithSlider(self):
		"""
		Update the window width and window level of the image according to the slider.
		"""
		parameterNode = self.getParameterNode()
		# Get the CT volume we want to modify
		inputVolume = parameterNode.GetNodeReference(self.INPUT_VOLUME)
		# if the volume is not loaded, return
		if inputVolume is None:
			return
		# Get the display node of the CT volume
		displayNode = inputVolume.GetDisplayNode()

		# Get the window width and window level from the parameter node
		ww = float(parameterNode.GetParameter(self.WINDOW_WIDTH))
		wl = float(parameterNode.GetParameter(self.WINDOW_LEVEL))
		# Allow us to change the window width and window level manually
		displayNode.AutoWindowLevelOff()
		# Update the display node
		displayNode.SetWindow(ww)
		displayNode.SetLevel(wl)

		# update the parameter node
		parameterNode.SetParameter(self.WINDOW_WIDTH, str(ww))
		parameterNode.SetParameter(self.WINDOW_LEVEL, str(wl))

	def CreateImageSlice(self):
		"""
		Create an image reslice.
		"""

		self.SetVolumeRangeTo_0_255()
		
		self.ChangeScalarTypeToUChar()

		self.CreateSlide()

	def SetVolumeRangeTo_0_255(self):
		"""
		Set the volume range to [0-255].
		"""
		parameterNode = self.getParameterNode()
		inputVolume = parameterNode.GetNodeReference(self.INPUT_VOLUME)
		imageArray = slicer.util.arrayFromVolume(inputVolume)

		# Get the window width and window level parameters
		displayNode = inputVolume.GetDisplayNode()
		windowWidth = displayNode.GetWindow()
		windowLevel = displayNode.GetLevel()
		lowerlimit = windowLevel - (windowWidth/2)
		# Update the image array with the new values
		imageArray = ((imageArray - lowerlimit)/windowWidth)*255
		#Clip the values to [0,255] range so that every value below 0 is set to 0 and every value above 255 is set to 255
		imageArray = np.clip(imageArray, 0,255)
		#Update the volume with the new values
		slicer.util.updateVolumeFromArray(inputVolume, imageArray)

	def ChangeScalarTypeToUChar(self):
		"""
		Change the type of image to UChar using the "Resample Image (BRAINS)" module.
		"""
		parameterNode = self.getParameterNode()
		inputVolume = parameterNode.GetNodeReference(self.INPUT_VOLUME)

		# Set all the parameters required for the cli module
		parameters = {}
		parameters["inputVolume"] = inputVolume.GetID()
		parameters["referenceVolume"] = 'None'
		outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", "UCharVolume")
		parameters["outputVolume"] = outputVolume.GetID()
		parameters["pixelType"] = "uchar"
		parameters["deformationVolume"] = 'None'
		identityTransform = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode", "Identity_T")
		parameters["warpTransform"] = identityTransform.GetID()
		parameters["interpolationMode"] = "Linear"
		parameters["inverseTransform"] = 'False'

		# Access the "Resample Image (BRAINS)" module and apply the parameters to it
		node  = slicer.cli.createNode(slicer.modules.brainsresample)
		resampleImageModule = slicer.modules.brainsresample
		slicer.cli.run(resampleImageModule, node, parameters, True) # Execute it

		slicer.mrmlScene.RemoveNode(slicer.util.getNode('Identity_T')) # We had to create an identity transform to run the process. Once we have finish, delete this transform from the scene

	def CreateSlide(self):
		"""
		Create the image reslice.
		"""
		parameterNode = self.getParameterNode()
		inputVolume = slicer.mrmlScene.GetFirstNodeByName("UCharVolume")

		observerTag = None
		outputSpacing = [1.0, 1.0, 1.0]  # Millimeters/pixel
		outputExtent = [0, 99, 0, 99, 0, 0] # First and last pixel indices along each axis

		'''
		Extent cannot be negative, because some Slicer components assume that extent starts at zero
		outputExtent = [-50, 49, -50, 49, 0, 0]
		Reslice and image data content will be correct, but Slicer will not display the negative extent of the slice.
		outputNode.ShiftImageDataExtentToZeroStart()
		would fix the problem once, but it cannot be used repeatedly with reslice transform modifications.
		'''

		# Compute reslice transformation

		volumeToIjkMatrix = vtk.vtkMatrix4x4()
		inputVolume.GetRASToIJKMatrix(volumeToIjkMatrix)

		sliceToRasTransform = vtk.vtkTransform()
		sliceToRasTransform.Translate(-100, -100, 0.0)
		sliceToRasTransform.RotateX(30)
		sliceToRasTransform.RotateY(30)

		sliceToIjkTransform = vtk.vtkTransform()
		sliceToIjkTransform.Concatenate(volumeToIjkMatrix)
		sliceToIjkTransform.Concatenate(sliceToRasTransform)

		# Use MRML node to modify transform in GUI
		sliceToRasNode = slicer.mrmlScene.GetFirstNodeByName("Image_T")
		if sliceToRasNode is None:
				sliceToRasNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLinearTransformNode", "Image_T")

		sliceToRasNode.SetAndObserveTransformToParent(sliceToRasTransform)

		# Run reslice to produce output image

		reslice = vtk.vtkImageReslice()
		reslice.SetInputData(inputVolume.GetImageData())
		reslice.SetResliceTransform(sliceToIjkTransform)
		reslice.SetInterpolationModeToLinear()
		reslice.SetOutputOrigin(0.0, 0.0, 0.0)  # Must keep zero so transform overlays slice with volume
		reslice.SetOutputSpacing(outputSpacing)
		reslice.SetOutputDimensionality(2)
		reslice.SetOutputExtent(outputExtent)
		reslice.SetBackgroundLevel(0)
		reslice.Update()
		reslice.GetOutput().SetSpacing(1,1,1)  # Spacing will be set on MRML node to let Slicer know

		# To allow re-run of this script, try to reuse exisiting node before creating a new one
		# Get the output node by ID instead
		outputNode = parameterNode.GetNodeReference(self.CT_RESLICE_OUTPUT)
		if outputNode is None:
				outputNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", self.CT_RESLICE_OUTPUT)
				# Add it to the parameter node, this way we can add it to the IGTLink output
				parameterNode.SetNodeReferenceID(self.CT_RESLICE_OUTPUT, outputNode.GetID())
				# get the node again, and print it
				outputNode = parameterNode.GetNodeReference(self.CT_RESLICE_OUTPUT)
		
		outputNode.SetAndObserveImageData(reslice.GetOutput())
		outputNode.SetSpacing(outputSpacing)
		outputNode.CreateDefaultDisplayNodes()
		displayNode = outputNode.GetDisplayNode()
		displayNode.AutoWindowLevelOff()
		displayNode.SetWindow(255)
		displayNode.SetLevel(128)

		# Transform output image so it is aligned with original volume

		outputNode.SetAndObserveTransformNodeID(sliceToRasNode.GetID())

		# Show and follow output image in red slice view

		redSliceWidget = slicer.app.layoutManager().sliceWidget("Red")
		redSliceWidget.sliceController().setSliceVisible(True)
		redSliceWidget.sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(outputNode.GetID())
		driver = slicer.modules.volumereslicedriver.logic()
		redView = slicer.util.getNode('vtkMRMLSliceNodeRed')
		driver.SetModeForSlice(driver.MODE_TRANSVERSE, redView)
		driver.SetDriverForSlice(outputNode.GetID(), redView)

		# Callback function for transform updates

		def UpdateReslice(event, caller):
				try:
						slicer.app.pauseRender()
						
						inputTransformId = inputVolume.GetTransformNodeID()
						if inputTransformId is not None:
								inputTransformNode = slicer.mrmlScene.GetNodeByID(inputTransformId)
								rasToVolumeMatrix = vtk.vtkMatrix4x4()
								inputTransformNode.GetMatrixTransformFromWorld(rasToVolumeMatrix)
								sliceToIjkTransform.Identity()
								sliceToIjkTransform.Concatenate(volumeToIjkMatrix)
								sliceToIjkTransform.Concatenate(rasToVolumeMatrix)
								sliceToIjkTransform.Concatenate(sliceToRasTransform)
						
						reslice.Update()
						reslice.GetOutput().SetSpacing(1,1,1)

				finally:
						slicer.app.resumeRender()

		if observerTag is not None:
				sliceToRasNode.RemoveObserver(observerTag)
				observerTag = None

		observerTag = sliceToRasNode.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent, UpdateReslice)

	def LoadModelFromFile(self, modelFilePath, modelFileName, colorRGB_array, visibility_bool):
		"""
		Load the model "modelFileName" from the specified folder. Set its color to colorRGB_array and enable its visibility according to visibility_bool
		"""
		#parameterNode = self.getParameterNode()
		#modelFilePath = parameterNode.GetParameter(self.MODELS_DIRECTORY)
		try:
				node = slicer.util.getNode(modelFileName)
		except:
				node = slicer.util.loadModel(os.path.join(modelFilePath, modelFileName))
				node.GetModelDisplayNode().SetColor(colorRGB_array)
				node.GetModelDisplayNode().SetVisibility(visibility_bool)
				#print (modelFileName + ' model loaded')

		return node        

	# Alicia function
	def LoadScrewModelsFromFile(self):
		"""
			First, delete preexisting screw models in the scene. Second, parse the screw transforms received from Unity and load the corresponding screw models from the specified folder
		"""
		parameterNode = self.getParameterNode()
		screwPath = parameterNode.GetParameter(self.SCREWS_DIRECTORY) # Get path to screw models

		modelNodes = slicer.util.getNodesByClass("vtkMRMLModelNode")
		for modelNode in modelNodes: # Everytime we click on the "Load screw models" button, we delete all screws in the scene. Then we create the new ones.
			if ("Screw" in modelNode.GetName()):
				slicer.mrmlScene.RemoveNode(modelNode)

		imageNode = slicer.util.getFirstNodeByName("Image_T")
		numberOfScrews = int(imageNode.GetAttribute("OpenIGTLink.NumOfScrews"))
		transformNodes = slicer.util.getNodesByClass("vtkMRMLLinearTransformNode")
		for i in range(len(transformNodes)):
			tNode = transformNodes[i]
			transformName = tNode.GetName()
			
			if ("Screw" in transformName):
				screwTransformNumber = int(tNode.GetAttribute("OpenIGTLink.ModelNumber"))

				if (screwTransformNumber > numberOfScrews):
					slicer.mrmlScene.RemoveNode(tNode) # If there are preexisting screw transforms corresponding to models that are not there anymore, delete them. For instance, if there were two screw transforms in the scene and
																						 # the user in HoloLens deletes one screw, the Screw-2_T won't be updated anymore, but it won't be deleted in 3D Slicer either. We use this lines to perform this process manually.
																						 # We receive the number of active screws in HoloLens through the "NumOfScrews" attribute. We compare the number of screws with the amount of transforms we have in Slicer. If there are
																						 # more transforms than screws, delete the extra ones

				else:
					screwName = tNode.GetAttribute("OriginalNodeName").split("_")[0]
					fileName = tNode.GetAttribute("OpenIGTLink.ModelName") # Get the model name
					modelColor = tNode.GetAttribute("OpenIGTLink.ModelColor") # Get the model color from the metadata of the transform message
					colorArray = np.asarray(modelColor.split(","), dtype=float) # Parse the color numbers as floats
					newScrew = self.LoadModelFromFile(screwPath, fileName, colorArray, True) # Load the corresponding model from file and assign to it its corresponding color
					newScrew.SetName(screwName) # Rename the model with the format Screw-1, Screw-2, etc.
					self.ApplyTransformToObject(newScrew, transformName) # Apply the transform to the model
					self.ApplyTransformToObject(tNode, "Spine_T") 
			
	def GetOrCreateTransform(self, transformName):
		"""
		Gets existing tranform or create new transform containing the identity matrix.
		"""
		try:
				node = slicer.util.getNode(transformName)
		except:
				node=slicer.vtkMRMLLinearTransformNode()
				node.SetName(transformName)
				slicer.mrmlScene.AddNode(node)
				#print ('ERROR: ' + transformName + ' transform was not found. Creating node as identity...')
		return node

	def ApplyTransformToObject(self, object, transformName):
		"""
		Apply "transformName" transform to "object"
		"""

		# Get transform
		transform  = self.GetOrCreateTransform(transformName)

		object.SetAndObserveTransformNodeID(transform.GetID())
		
		#print ('Transform ' + transformName + ' applied to ' + object.GetName())

		return transform

	def StartOIGTLConnection(self, port_tracker):
		"""
		Starts OIGTL connection.
		"""    
		parameterNode = self.getParameterNode()
		# Open connection
		try:
				cnode = slicer.util.getNode('IGTLConnector')
		except:
				cnode = slicer.vtkMRMLIGTLConnectorNode()
				slicer.mrmlScene.AddNode(cnode)
				cnode.SetName('IGTLConnector')
				#cnode.RegisterOutgoingMRMLNode(parameterNode.GetParameter(self.INPUT_VOLUME))
		status = cnode.SetTypeServer(port_tracker)
		
		# Check connection status
		if status == 1:
				cnode.Start()
				logging.debug('Connection Successful')
				# Add CT_reslice to the output of the connector
				parameterNode = self.getParameterNode()
				# Get the CT_RESLICE node from parameter node
				outputNode = parameterNode.GetNodeReference(self.CT_RESLICE_OUTPUT)
				# Add the node to the connector
				cnode.RegisterOutgoingMRMLNode(outputNode)

		
		else:
				print ('ERROR: Unable to activate server')
				logging.debug('ERROR: Unable to activate server')

		return status       

	def StopOIGTLConnection(self):
		"""
		Stops OIGTL connection.
		"""    
		cnode = slicer.util.getNode('IGTLConnector')
		cnode.Stop()     
	
	def SaveData(self):
		"""
		Save the data in the scene.
		""" 
		parameterNode = self.getParameterNode()

		# Get the Save Directory from slicer settings
		settings = slicer.app.userSettings()
		saveDirectory = settings.value(self.SAVING_DIRECTORY)

		patientID = parameterNode.GetParameter(self.PATIENT_ID)
		userID = parameterNode.GetParameter(self.USER_ID)
		spineModel_node = parameterNode.GetNodeReference(self.SPINE_MODEL)
		spineT_node = parameterNode.GetNodeReference(self.SPINE_TRANSFORM)

		# Extract data data
		currentDate = time.strftime("%Y-%m-%d_%H-%M-%S")
		
		# Saving folder path
		save_folder_path = os.path.join(saveDirectory, "Patient_00" + patientID, "User_" + userID)
		
		# Create the saving folder if it doesn't exist
		if not (os.path.exists(save_folder_path)):
				os.makedirs(save_folder_path)


		## Save the scene
		# Generate file name
		sceneName = "{}_{}_patient{}_user{}".format(currentDate, "Scene", patientID, userID)
		sceneSaveFilename = os.path.join(save_folder_path, sceneName + ".mrb")
		# Save scene
		if slicer.util.saveScene(sceneSaveFilename):
			logging.info("Scene saved to: {0}".format(sceneSaveFilename))
		else:
			logging.error("Scene saving failed")
		
		return save_folder_path
