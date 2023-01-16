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
			self.parent.title = "AR_Planner"  # TODO: make this more human readable by adding spaces
			self.parent.categories = ["PedicleScrewPlacementPlanner"]  # TODO: set categories (folders where the module shows up in the module selector)
			self.parent.dependencies = []  # TODO: add here list of module names that this module requires
			self.parent.contributors = ["Alicia Pose (Universidad Carlos III de Madrid) and David Morton (Queen's University)"]  # TODO: replace with "Firstname Lastname (Organization)"
			# TODO: update with short description of the module and a link to online module documentation
			self.parent.helpText = """
	This is an example of scripted loadable module bundled in an extension.
	See more information in <a href="https://github.com/organization/projectname#AR_Planner">module documentation</a>.
	"""
			# TODO: replace with organization, grant and thanks
			self.parent.acknowledgementText = """
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
			self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
			self.ui.modelsPath.connect("textChanged(QString)", self.updateParameterNodeFromGUI)
			self.ui.imageHistogramSlideBar.connect("valuesChanged(double,double)", self.updateParameterNodeFromGUI)
			self.ui.serverActiveCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
			self.ui.patientID_text.connect("textChanged(QString)", self.updateParameterNodeFromGUI)
			self.ui.userID_text.connect("textChanged(QString)", self.updateParameterNodeFromGUI)
			self.ui.repetitionNumber_text.connect("textChanged(QString)", self.updateParameterNodeFromGUI)

			# self.ui.savingPath.connect("textChanged(QString)", self.updateParameterNodeFromGUI)
			self.ui.savingPath.connect('directorySelected(QString)', self.onSaveDirectoryChanged)

			self.ui.saveDataButton.connect("clicked(bool)", self.updateParameterNodeFromGUI)

			# Buttons
			self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onChangeInputVolumeClicked)
			self.ui.imageHistogramSlideBar.connect("valuesChanged(double,double)", self.onImageValuesUpdatedWithSlider)
			self.ui.createImageSlideButton.connect('clicked(bool)', self.onCreateImageSlideClicked)
			self.ui.loadSpineModelButton.connect('clicked(bool)', self.onLoadSpineModelFromFileClicked)
			self.ui.loadScrewModelsButton.connect('clicked(bool)', self.onLoadScrewModelsFromFileClicked)
			self.ui.serverActiveCheckBox.connect("toggled(bool)", self.onActivateOpenIGTLinkConnectionClicked)
			self.ui.saveDataButton.connect('clicked(bool)', self.onSaveDataClicked)

			# Make sure parameter node is initialized (needed for module reload)
			self.initializeParameterNode()
			self.initializeGUI() # This is an addition to avoid initializing parameter node before connections
			# self.updateWidgetsForCurrentVolume()
			# self.onResetNeedleButton()

	def initializeGUI(self):
		# initailize the save directory using settings
		settings = slicer.app.userSettings()
		if settings.value(self.logic.SAVING_DIRECTORY): # if the settings exists
			self.ui.savingPath.directory = settings.value(self.logic.SAVING_DIRECTORY)

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
			# if not self._parameterNode.GetNodeReference(self.logic.SAVING_DIRECTORY):
			# 		savingPath = "C:\temp"
			# 		self._parameterNode.SetParameter(self.logic.SAVING_DIRECTORY, savingPath)

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
			'''
			#self.ui.imageHistogramSlideBar.minimumValue = float(float(self._parameterNode.GetParameter(self.logic.WINDOW_LEVEL)) - (float(self._parameterNode.GetParameter(self.logic.WINDOW_WIDTH)))/2)
			#self.ui.imageHistogramSlideBar.maximumValue = float(float(self._parameterNode.GetParameter(self.logic.WINDOW_LEVEL)) + (float(self._parameterNode.GetParameter(self.logic.WINDOW_WIDTH)))/2)
			#self.ui.image_WW.value = float(self._parameterNode.GetParameter(self.logic.WINDOW_WIDTH))
			#self.ui.image_WL.value = float(self._parameterNode.GetParameter(self.logic.WINDOW_LEVEL))
			'''
			
			# Update buttons states and tooltips
			if self._parameterNode.GetNodeReference("InputVolume"):
					self.ui.createImageSlideButton.toolTip = "Compute output volume"
					self.ui.createImageSlideButton.enabled = True
			else:
					self.ui.createImageSlideButton.toolTip = "Select input volume nodes"
					self.ui.createImageSlideButton.enabled = False

			if (self._parameterNode.GetParameter(self.logic.PATIENT_ID)=='') | (self._parameterNode.GetParameter(self.logic.USER_ID)=='') | (self._parameterNode.GetParameter(self.logic.REPETITION_NUMBER)==''):
					self.ui.saveDataButton.toolTip = "Set patient, user and repetition number"
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
			
			self.ui.image_WW.value = float(self._parameterNode.GetParameter(self.logic.WINDOW_WIDTH))
			self.ui.image_WL.value = float(self._parameterNode.GetParameter(self.logic.WINDOW_LEVEL))

			self._parameterNode.SetParameter(self.logic.ACTIVE_SERVER_CHECKBOX, "true" if self.ui.serverActiveCheckBox.checked else "false")
			self._parameterNode.SetParameter(self.logic.PATIENT_ID, (self.ui.patientID_text).text)
			self._parameterNode.SetParameter(self.logic.USER_ID, (self.ui.userID_text).text)
			self._parameterNode.SetParameter(self.logic.REPETITION_NUMBER, (self.ui.repetitionNumber_text).text)
			(dirname, spineFileName) = os.path.split(self.ui.modelsPath.currentPath)
			self._parameterNode.SetParameter(self.logic.MODELS_DIRECTORY, dirname)
			self._parameterNode.SetParameter(self.logic.SPINE_FILENAME, spineFileName)
			
			# self._parameterNode.SetParameter(self.logic.SAVING_DIRECTORY, self.ui.savingPath.directory)
			self._parameterNode.EndModify(wasModified)




	def onChangeInputVolumeClicked(self):
			self.updateParameterNodeFromGUI()
			self.logic.UpdateImageLimits()
			
			self.ui.imageHistogramSlideBar.minimum = float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_minLimit))
			self.ui.imageHistogramSlideBar.maximum = float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_maxLimit))
							
			self.ui.image_WW.maximum = float(float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_maxLimit)) - float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_minLimit)))
			self.ui.image_WW.minimum = 0.0
			self.ui.image_WL.maximum = float(float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_maxLimit)) - float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_minLimit)))/2
			self.ui.image_WL.minimum = float(self._parameterNode.GetParameter(self.logic.IMAGE_HIST_SLIDEBAR_minLimit))
		


	def onImageValuesUpdatedWithSlider(self, lower, upper):
			self.updateParameterNodeFromGUI()
			self.logic.UpdateImageValuesWithSlider(lower, upper)

	

	def onCreateImageSlideClicked(self):
			"""
			Run processing when user clicks "Create Image Slide" button.
			"""
			self.updateParameterNodeFromGUI()
			with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

					# Compute output
					self.ui.imageSliceName.text = "Image slice name: " + self.logic.CreateImageSlide()

					self.ui.InputImageCollapsibleButton.collapsed = True


	def onLoadSpineModelFromFileClicked(self):
		"""
		Run processing when user clicks "Load Models" button.
		"""
		self.updateParameterNodeFromGUI()
		with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

				parameterNode = self.logic.getParameterNode()
				# Load spine model and change its color
				spineFileName = parameterNode.GetParameter(self.logic.SPINE_FILENAME)
				boneColor = np.array([241,214,145])/255
				spineModel = self.logic.LoadModelFromFile(spineFileName, boneColor, True)
				self._parameterNode.SetNodeReferenceID(self.logic.SPINE_MODEL, spineModel.GetID()) ## Update parameter node
				
				### Build transform tree        
				spineTransformName = "Spine_T"
				spineTransform = self.logic.ApplyTransformToObject(spineModel, spineTransformName)
				self._parameterNode.SetNodeReferenceID(self.logic.SPINE_TRANSFORM, spineTransform.GetID()) ## Update parameter node

				imageTransform = slicer.util.getFirstNodeByName("Image_T")
				self.logic.ApplyTransformToObject(imageTransform, spineTransformName)

				self.ui.loadSpineModelButton.enabled = False

	def onLoadScrewModelsFromFileClicked(self):
		self.updateParameterNodeFromGUI()
		self.logic.LoadScrewModelsFromFile()

	
	def onActivateOpenIGTLinkConnectionClicked(self, connect):
		self.updateParameterNodeFromGUI()
		# Update connection 
		if connect:
				port_tracker = 18944
				status = self.logic.StartOIGTLConnection(port_tracker) # Start connection
				if status == 1:
						self.connect = False
						self.ui.OIGTLconnectionLabel.text = "OpenIGTLink server - ACTIVE"
		else:
				self.logic.StopOIGTLConnection() # Stop connection
				connect = True
				self.ui.OIGTLconnectionLabel.text = "OpenIGTLink server - INACTIVE"
				

	# Saving results
	def onSaveDirectoryChanged(self, directory):
		# update settings with the new directory
		settings = slicer.app.userSettings()
		settings.setValue(self.logic.SAVING_DIRECTORY, directory)
		print("Saving directory changed to: " + directory)

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
# AR_PlannerLogic
#

class AR_PlannerLogic(ScriptedLoadableModuleLogic, VTKObservationMixin):
	"""This class should implement all the actual
	computation done by your module.  The interface
	should be such that other python code can import
	this class and make use of the functionality without
	requiring an instance of the Widget.
	Uses ScriptedLoadableModuleLogic base class, available at:
	https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
	"""

	# Image slide
	INPUT_VOLUME = 'InputVolume'
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

	# Transforms
	SPINE_TRANSFORM = 'Spine_T'
	IMAGE_TRANSFORM = 'Image_T'

	# Saving path
	SAVING_DIRECTORY = 'savingPath'
	PATIENT_ID = 'PatientID'
	USER_ID = 'UserID'
	REPETITION_NUMBER = 'RepetitionNumber'






	def __init__(self):
			"""
			Called when the logic class is instantiated. Can be used for initializing member variables.
			"""
			ScriptedLoadableModuleLogic.__init__(self)

	def setDefaultParameters(self, parameterNode):
			"""
			Initialize parameter node with default settings.
			"""
			if not parameterNode.GetParameter(self.WINDOW_WIDTH):
					parameterNode.SetParameter(self.WINDOW_WIDTH, "0")
			if not parameterNode.GetParameter(self.WINDOW_LEVEL):
					parameterNode.SetParameter(self.WINDOW_LEVEL, "0")
			if not parameterNode.GetParameter(self.ACTIVE_SERVER_CHECKBOX):
					parameterNode.SetParameter(self.ACTIVE_SERVER_CHECKBOX, "0")

	'''
	@vtk.calldata_type(vtk.VTK_OBJECT)
	def onNodeAdded(self, caller, event, calldata):
			node = calldata
			if ("Screw" in node.GetName()):
					print(node.GetName())
					self.addObserver(node, slicer.vtkMRMLTransformableNode.TransformModifiedEvent, self.onScrewTransformModified)


	def onScrewTransformModified(self, caller, event):
		if caller is None:
			logging.warning('onScrewTransformModified failed: no transform node')
		else:
			transformNode = caller
			self.UpdateModelForTransform(transformNode)
	'''
		



	def UpdateImageLimits(self):
			parameterNode = self.getParameterNode()
			inputVolume = parameterNode.GetNodeReference(self.INPUT_VOLUME)
			
			imageArray = slicer.util.arrayFromVolume(inputVolume)
			minValue = imageArray.min()
			maxValue = imageArray.max()

			parameterNode.SetParameter(self.IMAGE_HIST_SLIDEBAR_minLimit, str(minValue))
			parameterNode.SetParameter(self.IMAGE_HIST_SLIDEBAR_maxLimit, str(maxValue))

			

	def UpdateImageValuesWithSlider(self, lower, upper):
			parameterNode = self.getParameterNode()
			inputVolume = parameterNode.GetNodeReference(self.INPUT_VOLUME)
			
			displayNode = inputVolume.GetDisplayNode()
			windowWidth = upper - lower
			windowLevel = lower+(windowWidth/2)

			displayNode.SetWindow(windowWidth)
			displayNode.SetLevel(windowLevel)
			
			parameterNode.SetParameter(self.WINDOW_WIDTH, str(windowWidth))
			parameterNode.SetParameter(self.WINDOW_LEVEL, str(windowLevel))

	def UpdateWWvalue(self, ww_value):
			parameterNode = self.getParameterNode()

			inputVolume = parameterNode.GetNodeReference(self.INPUT_VOLUME)        
			displayNode = inputVolume.GetDisplayNode()
			displayNode.SetWindow(ww_value)
			print(ww_value)

			parameterNode.SetParameter(self.WINDOW_WIDTH, str(ww_value))

	def UpdateWLvalue(self, wl_value):
			parameterNode = self.getParameterNode()

			inputVolume = parameterNode.GetNodeReference(self.INPUT_VOLUME)        
			displayNode = inputVolume.GetDisplayNode()
			displayNode.SetLevel(wl_value)

			parameterNode.SetParameter(self.WINDOW_LEVEL, str(wl_value))




			

	def CreateImageSlide(self):

			self.SetVolumeRangeTo_0_255()
			
			self.ChangeScalarTypeToUChar()

			imageSliceNameLabel = self.CreateSlide()
			return imageSliceNameLabel


	def SetVolumeRangeTo_0_255(self):
			parameterNode = self.getParameterNode()
			inputVolume = parameterNode.GetNodeReference(self.INPUT_VOLUME)
			imageArray = slicer.util.arrayFromVolume(inputVolume)

			displayNode = inputVolume.GetDisplayNode()
			windowWidth = displayNode.GetWindow()
			windowLevel = displayNode.GetLevel()
			lowerlimit = windowLevel - (windowWidth/2)
			upperlimit = windowLevel + (windowWidth/2)
			imageArray = ((imageArray - lowerlimit)/windowWidth)*255

			## Step 4: CODE: Clip the values to [0,255] range so that every value below 0 is set to 0 and every value above 255 is set to 255
			imageArray = np.clip(imageArray, 0,255)

			## Step 5: CODE: Update the volume with the new values
			slicer.util.updateVolumeFromArray(inputVolume, imageArray)

	def ChangeScalarTypeToUChar(self):
			parameterNode = self.getParameterNode()
			inputVolume = parameterNode.GetNodeReference(self.INPUT_VOLUME)

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


			node  = slicer.cli.createNode(slicer.modules.brainsresample)
			resampleImageModule = slicer.modules.brainsresample
			slicer.cli.run(resampleImageModule, node, parameters, True)

			slicer.mrmlScene.RemoveNode(slicer.util.getNode('Identity_T'))


	def CreateSlide(self):
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

			outputNodeName = "CT_slide"
			outputNode = slicer.mrmlScene.GetFirstNodeByName(outputNodeName)
			if outputNode is None:
					outputNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", outputNodeName)

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

			return outputNodeName


	def LoadModelFromFile(self, modelFileName, colorRGB_array, visibility_bool):
			parameterNode = self.getParameterNode()
			modelFilePath = parameterNode.GetParameter(self.MODELS_DIRECTORY)
			try:
					node = slicer.util.getNode(modelFileName)
			except:
					node = slicer.util.loadModel(os.path.join(modelFilePath, modelFileName))
					node.GetModelDisplayNode().SetColor(colorRGB_array)
					node.GetModelDisplayNode().SetVisibility(visibility_bool)
					#print (modelFileName + ' model loaded')

			return node        

	def LoadScrewModelsFromFile(self):
		modelNodes = slicer.util.getNodesByClass("vtkMRMLModelNode")
		for modelNode in modelNodes:
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
					slicer.mrmlScene.RemoveNode(tNode)

				else:
					screwName = tNode.GetAttribute("OriginalNodeName").split("_")[0]
					fileName = tNode.GetAttribute("OpenIGTLink.ModelName")
					modelColor = tNode.GetAttribute("OpenIGTLink.ModelColor") # Get the model color from the metadata of the transform message
					colorArray = np.asarray(modelColor.split(","), dtype=float) # Parse the color numbers as floats
					newScrew = self.LoadModelFromFile(fileName, colorArray, True) # Load the corresponding model from file and assign to it its corresponding color
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
			
			print ('Transform ' + transformName + ' applied to ' + object.GetName())

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
			parameterNode = self.getParameterNode()
			# save_selected_folder_path = parameterNode.GetParameter(self.SAVING_DIRECTORY) # This uses the parameter node when it should use settings

			# Get the Save Directory from slicer settings
			settings = slicer.app.userSettings()
			saveDirectory = settings.value(self.SAVING_DIRECTORY)

			patientID = parameterNode.GetParameter(self.PATIENT_ID)
			userID = parameterNode.GetParameter(self.USER_ID)
			repetitionNumber = parameterNode.GetParameter(self.REPETITION_NUMBER)
			spineModel_node = parameterNode.GetNodeReference(self.SPINE_MODEL)
			spineT_node = parameterNode.GetNodeReference(self.SPINE_TRANSFORM)

			# Extract current data
			currentDate = time.strftime("%Y-%m-%d_%H-%M-%S")
			
			# Saving folder paths
			# save_folder_path = os.path.join(save_selected_folder_path, "Patient_00" + patientID, "User_" + userID, "Repetition_" + repetitionNumber)
			save_folder_path = os.path.join(saveDirectory, "Patient_00" + patientID, "User_" + userID)

			

			# Create the saving folder if it doesn't exist
			if not (os.path.exists(save_folder_path)):
					os.makedirs(save_folder_path)


			## Save the scene
			# Generate file name
			sceneName = "{}_{}_patient{}_user{}_repNumber{}".format(currentDate, "Scene", patientID, userID, repetitionNumber)
			sceneSaveFilename = os.path.join(save_folder_path, sceneName + ".mrb")
			# Save scene
			if slicer.util.saveScene(sceneSaveFilename):
				logging.info("Scene saved to: {0}".format(sceneSaveFilename))
			else:
				logging.error("Scene saving failed")

			
			return save_folder_path
