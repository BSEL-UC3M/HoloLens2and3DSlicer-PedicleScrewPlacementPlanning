import logging
import os
from xml.etree.ElementTree import QName
import numpy as np
import vtk

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import time

#
# Desktop_Planner_Module
#

class Desktop_Planner(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Desktop_Planner"
    self.parent.categories = ["PedicleScrewPlacementPlanner"]
    self.parent.contributors = ["Alicia Pose (Universidad Carlos III de Madrid) and David Morton (Queen's University)"]
    """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
    """


#
# Desktop_PlannerModuleWidget
#

class Desktop_PlannerWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  LAYOUT_DUAL3D = 101

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False
    self.screwNumber = 0

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/Desktop_Planner.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = Desktop_PlannerLogic()
    self.logic.setupScene()

    self.setupCustomLayout()

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).
    
    # VOLUME SELECTION
    self.ui.inputVolumeComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.onInputVolumeSelected)

    # SPINE SELECTION
    self.ui.spineModelComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.onSpineModelSelected)
    self.ui.loadScrewButton.connect('clicked(bool)', self.onLoadSpineButtonClicked)
    
    # SCREW SELECTION
    # The screw length and diameter are initizalied in the wigit viewer directly
    self.ui.loadScrewButton.connect('clicked(bool)', self.onLoadScrewButtonClicked)
    self.ui.screwTransformComboBox.connect('currentNodeChanged(vtkMRMLNode*)', self.onScrewTransformSelected)


    # Translation
    self.ui.leftButton.connect('clicked(bool)', self.onLeftButton)
    self.ui.rightButton.connect('clicked(bool)', self.onRightButton)
    self.ui.upButton.connect('clicked(bool)', self.onUpButton)
    self.ui.downButton.connect('clicked(bool)', self.onDownButton)
    self.ui.inButton.connect('clicked(bool)', self.onInButton)
    self.ui.outButton.connect('clicked(bool)', self.onOutButton)
    self.ui.screwInLargeButton.connect('clicked(bool)', self.onInLargeButton)
    self.ui.screwOutLargeButton.connect('clicked(bool)', self.onOutLargeButton)
    # Rotation
    self.ui.cranialRotationButton.connect('clicked(bool)', self.onCranialRotationButton)
    self.ui.caudalRotationButton.connect('clicked(bool)', self.onCaudalRotationButton)
    self.ui.leftRotationButton.connect('clicked(bool)', self.onLeftRotationButton)
    self.ui.rightRotationButton.connect('clicked(bool)', self.onRightRotationButton)
    # Slider changes
    self.ui.leftRightSlider.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.ui.upDownSlider.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.ui.cranialRotationSlider.connect("valueChanged(double)", self.updateParameterNodeFromGUI)
    self.ui.leftRotationSlider.connect("valueChanged(double)", self.updateParameterNodeFromGUI)

    # Reset buttons
    self.ui.resetScrewButton.connect('clicked(bool)', self.onResetScrewButton)
    self.ui.resetViewsButton.connect('clicked(bool)', self.resetViews)
    
    # SAVING RESULTS
    self.ui.saveDirectoryButton.connect('directorySelected(QString)', self.onSaveDirectoryChanged)
    self.ui.userIDLineEdit.connect('textChanged(QString)', self.onUserIDChanged)
    self.ui.patientIDLineEdit.connect('textChanged(QString)', self.onPatientIDChanged)
    self.ui.saveButton.connect('clicked(bool)', self.onSaveButton)

    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()
    self.initializeGUI() # This is an addition to avoid initializing parameter node before connections
    self.updateWidgetsForCurrentVolume()
    self.onResetScrewButton()

  def initializeGUI(self):
    # initailize the save directory using settings
    settings = slicer.app.userSettings()
    if settings.value(self.logic.RESULTS_SAVE_DIRECTORY_SETTING): # if the settings exists
      self.ui.saveDirectoryButton.directory = settings.value(self.logic.RESULTS_SAVE_DIRECTORY_SETTING)

  def setupCustomLayout(self):
    customLayout = \
      """
      <layout type="horizontal">
        <item>
          <view class="vtkMRMLViewNode" singletontag="1">
            <property name="viewLabel" action="default">1</property>
          </view>
        </item>
        <item>
          <view class="vtkMRMLViewNode" singletontag="2" type="secondary">
            <property name="viewlabel" action="default">2</property>
          </view>
        </item>
      </layout>
      """
    # Built-in layout IDs are all below 100, so you can choose any large random number
    # for your custom layout ID.
    layoutManager = slicer.app.layoutManager()
    layoutManager.layoutLogic().GetLayoutNode().AddLayoutDescription(self.LAYOUT_DUAL3D, customLayout)

  
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

    # Update widgets from parameter node

    currentInputVolume = self.ui.inputVolumeComboBox.currentNode()
    referencedVolume = self._parameterNode.GetNodeReference(self.logic.CURRENT_INPUT_VOLUME)
    if currentInputVolume != referencedVolume:
      self.ui.inputVolumeComboBox.setCurrentNode(referencedVolume)

    currentScrewTransform = self.ui.screwTransformComboBox.currentNode()
    referencedTransform = self._parameterNode.GetNodeReference(self.logic.SCREW_TO_RAS_TRANSFORM)
    if currentScrewTransform != referencedTransform:
      self.ui.screwTransformComboBox.setCurrentNode(referencedTransform)

    # update the sliders from the parameter node
    self.ui.leftRightSlider.value = float(self._parameterNode.GetParameter(self.logic.TRANSLATE_R))
    self.ui.upDownSlider.value = float(self._parameterNode.GetParameter(self.logic.TRANSLATE_S))
    self.ui.cranialRotationSlider.value = float(self._parameterNode.GetParameter(self.logic.ROTATE_R))
    self.ui.leftRotationSlider.value = float(self._parameterNode.GetParameter(self.logic.ROTATE_S))

    # update patient ID
    self.ui.patientIDLineEdit.text = self._parameterNode.GetParameter(self.logic.PATIENT_ID)

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateWidgetsForCurrentVolume(self):
    """
    Update widget parameters that depend on the size and position of current volume.
    """
    usVolume = self._parameterNode.GetNodeReference(self.logic.CURRENT_INPUT_VOLUME)
    if usVolume is None:
      return

    bounds = np.zeros(6)
    usVolume.GetRASBounds(bounds)

    # Update sliders to cover the volumem with extra margins

    self.ui.leftRightSlider.minimum = bounds[0] - self.logic.MOTION_MARGIN
    self.ui.leftRightSlider.maximum = bounds[1] + self.logic.MOTION_MARGIN
    self.ui.upDownSlider.minimum = bounds[4] - self.logic.MOTION_MARGIN
    self.ui.upDownSlider.maximum = bounds[5] + self.logic.MOTION_MARGIN

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

    self._parameterNode.SetParameter(self.logic.TRANSLATE_R, str(self.ui.leftRightSlider.value))
    self._parameterNode.SetParameter(self.logic.TRANSLATE_S, str(self.ui.upDownSlider.value))
    self._parameterNode.SetParameter(self.logic.ROTATE_R, str(self.ui.cranialRotationSlider.value))
    self._parameterNode.SetParameter(self.logic.ROTATE_S, str(self.ui.leftRotationSlider.value))
    self.logic.updateTransformFromParameterNode()

    self._parameterNode.EndModify(wasModified)

  def onInputVolumeSelected(self, selectedNode):
    """
    This method is called when the user selects a new input volume
    """
    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    previousReferencedNode = self._parameterNode.GetNodeReference(self.logic.CURRENT_INPUT_VOLUME)

    if selectedNode is None:
      self._parameterNode.SetNodeReferenceID(self.logic.CURRENT_INPUT_VOLUME, "")
    else:
      self._parameterNode.SetNodeReferenceID(self.logic.CURRENT_INPUT_VOLUME, selectedNode.GetID())

    if previousReferencedNode == selectedNode or selectedNode is None:
      return

    self.updateWidgetsForCurrentVolume()

  def onSpineModelSelected(self, selectedNode):
    """
    This method is called when the user selects a new spine model
    """
    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    if selectedNode is None:
      self._parameterNode.SetNodeReferenceID(self.logic.SPINE_MODEL, "")
    else:
      self._parameterNode.SetNodeReferenceID(self.logic.SPINE_MODEL, selectedNode.GetID())

  def onLoadSpineButtonClicked(self):
    '''
    This method is called "Load spine" button is clicked
    '''
    pass

  def onLoadScrewButtonClicked(self):
    '''
    This method is called "Load screw model" button is clicked
    '''
    self.updateParameterNodeFromGUI()
    # screwName = self.ui.modelNameBox.currentText
    # Get the screw name from the length and diameter boxes instead
    screwLength = self.ui.screwLengthBox.currentText
    screwDiameter = self.ui.screwDiameterBox.currentText
    # If D = 5 and L = 30, then screwName = D5L30
    screwName = "D" + screwDiameter + "L" + screwLength
    #screwTransformName = self.ui.screwTransformComboBox.currentNode().GetName()
    self.screwNumber = self.screwNumber + 1
    screwTransformName = "Screw-" + str(self.screwNumber) + "_T"
    screwNode = self.logic.LoadScrewModel(screwName, screwTransformName)
    screwTransformNode = slicer.util.getFirstNodeByName(screwTransformName)
    self.ui.screwTransformComboBox.setCurrentNode(screwTransformNode)
    # set the screw parameters as an attribute of the model
    screwNode.SetAttribute("ScrewNumber", screwName)


  def onScrewTransformSelected(self, selectedNode):
    '''
    This method is called when a new transform is selected in the "Screw transform" menu
    '''
    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    if selectedNode is None:
      self._parameterNode.SetNodeReferenceID(self.logic.SCREW_TO_RAS_TRANSFORM, "")
    else:
      self._parameterNode.SetNodeReferenceID(self.logic.SCREW_TO_RAS_TRANSFORM, selectedNode.GetID())

    self.logic.updateParameterNodeFromTransform()
    self.logic.updateTransformFromParameterNode()

    self.logic.ResliceDriverToScrew(selectedNode.GetID())

  def onResetScrewButton(self):
    '''
    This function resets the position and orientation of the screw to default values determined by the current volume size
    '''
    # The slider ranges are set according to the current volume
    # Reset the screw location to the midpont of the slider range
    # Get min and max of the slider range
    minR = self.ui.leftRightSlider.minimum
    maxR = self.ui.leftRightSlider.maximum
    minS = self.ui.upDownSlider.minimum
    maxS = self.ui.upDownSlider.maximum
    # Set the translations in parameter node to midpoints
    self._parameterNode.SetParameter(self.logic.TRANSLATE_R, str(round((maxR + minR) / 2)))
    self._parameterNode.SetParameter(self.logic.TRANSLATE_S, str(round((maxS + minS) / 2)))
    # Set the rotations to 0
    self._parameterNode.SetParameter(self.logic.ROTATE_R, str(90))
    self._parameterNode.SetParameter(self.logic.ROTATE_S, str(0))

    # If there is a volume, make the screw as far back as possible, else make it 0
    usVolume = self._parameterNode.GetNodeReference(self.logic.CURRENT_INPUT_VOLUME)
    if usVolume is None:
      self._parameterNode.SetParameter(self.logic.TRANSLATE_A, str(0))
    else:
      bounds = np.zeros(6)
      usVolume.GetRASBounds(bounds)
      self._parameterNode.SetParameter(self.logic.TRANSLATE_A, str(bounds[2]))

    # update the transform
    self.logic.updateTransformFromParameterNode()

  

  # Tranlation
  def onRightButton(self):
    '''
    This method is called when the "Right" button in translation section is clicked
    '''
    self.ui.leftRightSlider.value = self.ui.leftRightSlider.value + self.logic.STEP_SIZE_TRANSLATION

  def onLeftButton(self):
    '''
    This method is called when the "Left" button in translation section is clicked
    '''
    self.ui.leftRightSlider.value = self.ui.leftRightSlider.value - self.logic.STEP_SIZE_TRANSLATION

  def onUpButton(self):
    '''
    This method is called when the ""Up"" button is clicked
    '''
    self.ui.upDownSlider.value = self.ui.upDownSlider.value + self.logic.STEP_SIZE_TRANSLATION

  def onDownButton(self):
    '''
    This method is called when the "Down" button is clicked
    '''
    self.ui.upDownSlider.value = self.ui.upDownSlider.value - self.logic.STEP_SIZE_TRANSLATION

  def onInButton(self):
    '''
    This method is called when the "In 1 mm" button is clicked
    '''
    self.logic.moveScrewIn(1)

  def onInLargeButton(self):
    '''
    This method is called when the "In 10 mm" button is clicked
    '''
    self.logic.moveScrewIn(10)

  def onOutButton(self):
    '''
    This method is called when the "Out 1 mm" button is clicked
    '''
    self.logic.moveScrewIn(-1)

  def onOutLargeButton(self):
    '''
    This method is called when the "Out 10 mm" button is clicked
    '''
    self.logic.moveScrewIn(-10)

  # Rotation
  def onCranialRotationButton(self):
    '''
    This method is called when the "Cranial" button is clicked
    '''
    self.ui.cranialRotationSlider.value = self.ui.cranialRotationSlider.value + self.logic.STEP_SIZE_ROTATION

  def onCaudalRotationButton(self):
    '''
    This method is called when the "Caudal" button is clicked
    '''
    self.ui.cranialRotationSlider.value = self.ui.cranialRotationSlider.value - self.logic.STEP_SIZE_ROTATION

  def onLeftRotationButton(self):
    '''
    This method is called when the "Left" button in rotation section is clicked
    '''
    self.ui.leftRotationSlider.value = self.ui.leftRotationSlider.value - self.logic.STEP_SIZE_ROTATION

  def onRightRotationButton(self):
    '''
    This method is called when the "Right" button in rotation section is clicked
    '''
    self.ui.leftRotationSlider.value = self.ui.leftRotationSlider.value + self.logic.STEP_SIZE_ROTATION

  # Reset view
  def resetViews(self):
      '''
      Resets the virtual camera positions
      '''
      layoutManager = slicer.app.layoutManager()
      layoutManager.setLayout(self.LAYOUT_DUAL3D)

      # Setup 3D view 0
      threeDWidget = layoutManager.threeDWidget(0)
      threeDView = threeDWidget.threeDView()
      threeDView.resetFocalPoint()
      threeDView.rotateToViewAxis(2)
      viewNode = threeDView.mrmlViewNode()
      viewNode.SetOrientationMarkerType(viewNode.OrientationMarkerTypeHuman)
      viewNode.SetOrientationMarkerSize(1)
      viewNode.SetBoxVisible(False)
      viewNode.SetAxisLabelsVisible(False)

      # Setup 3D view 1
      threeDWidget = layoutManager.threeDWidget(1)
      threeDView = threeDWidget.threeDView()
      threeDView.resetFocalPoint()
      threeDView.rotateToViewAxis(0)
      viewNode = threeDView.mrmlViewNode()
      viewNode.SetOrientationMarkerType(viewNode.OrientationMarkerTypeHuman)
      viewNode.SetOrientationMarkerSize(1)
      viewNode.SetBoxVisible(False)
      viewNode.SetAxisLabelsVisible(False)
 
  # Saving results
  def onSaveDirectoryChanged(self, directory):
    '''
    This method is called when the saving directory is updated
    '''
    # update settings with the new directory
    settings = slicer.app.userSettings()
    settings.setValue(self.logic.RESULTS_SAVE_DIRECTORY_SETTING, directory)
    
  def onUserIDChanged(self, userID):
    '''
    This method is called when the User ID field is updated
    '''
    # update the user ID in the parameter node
    self._parameterNode.SetParameter(self.logic.USER_ID, userID)
  
  def onPatientIDChanged(self, patientID):
    '''
    This method is called when the Patient ID field is updated
    '''
    # update the onPatientIDChanged ID in the parameter node
    self._parameterNode.SetParameter(self.logic.PATIENT_ID, patientID) 

  def onSaveButton(self):
    '''
    This method is called "Save Results" button is clicked
    '''
    self.logic.saveResults()

  


#
# Desktop_PlannerLogic
#

class Desktop_PlannerLogic(ScriptedLoadableModuleLogic):
  CURRENT_INPUT_VOLUME = "CurrentInputVolume"
  MOTION_MARGIN = 100  # Allow screw to go outside image volume by this many mm
  STEP_SIZE_TRANSLATION = 1  # Translation single click in mm
  STEP_SIZE_ROTATION = 1  # Rotation single click in degrees

  SCREW_TO_RAS_TRANSFORM = "ScrewToRasTransform"
  SCREW_MODEL = "ScrewModel"
  TRANSLATE_R = "TranslateR"
  TRANSLATE_A = "TranslateA"
  TRANSLATE_S = "TranslateS"
  ROTATE_R = "RotateR"
  ROTATE_S = "RotateS"

  RESULTS_SAVE_DIRECTORY_SETTING = 'Desktop_Planner/ResultsSaveDirectory'
  USER_ID = "UserID"
  PATIENT_ID = "PatientID"
  screwNumber = 0

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)
    self.SCREW_TRANSFORM = "screw_RAStoScrew"
    self.SCREW_TIP = "screwTip"

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    # Set Translate R
    if not parameterNode.GetParameter(self.TRANSLATE_R):
      parameterNode.SetParameter(self.TRANSLATE_R, "0")
    # Set Translate A
    if not parameterNode.GetParameter(self.TRANSLATE_A):
      parameterNode.SetParameter(self.TRANSLATE_A, "0")
    # Set Translate S
    if not parameterNode.GetParameter(self.TRANSLATE_S):
      parameterNode.SetParameter(self.TRANSLATE_S, "0")
    # Set Rotate R
    if not parameterNode.GetParameter(self.ROTATE_R):
      parameterNode.SetParameter(self.ROTATE_R, "0")
    # Set Rotate S
    if not parameterNode.GetParameter(self.ROTATE_S):
      parameterNode.SetParameter(self.ROTATE_S, "0")
    pass

  def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True): ######################################################################################## DO WE NEED THIS???
    pass

  def setupScene(self):
    """
    Set up the scene
    """
    parameterNode = self.getParameterNode()

    # If ScrewToRasTransform is not in the scene, create and add it
    screwToRasTransform = slicer.util.getFirstNodeByName(self.SCREW_TO_RAS_TRANSFORM)  # ***
    if screwToRasTransform is None:
      screwToRasTransform = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLinearTransformNode', self.SCREW_TO_RAS_TRANSFORM)
      parameterNode.SetNodeReferenceID(self.SCREW_TO_RAS_TRANSFORM, screwToRasTransform.GetID())

    t90Node=slicer.vtkMRMLLinearTransformNode()
    t90Node.SetName("RotationT")
    slicer.mrmlScene.AddNode(t90Node)

  def previousScene(self): ################################################################################################################################################################ DO WE NEED THIS?
    pass

  def nextScene(self): ################################################################################################################################################################ DO WE NEED THIS?
    pass

  def updateTransformFromParameterNode(self):
    """
    Update the transform from the parameter node
    """
    parameterNode = self.getParameterNode()  # Get the parameter node

    # apply the translation and rotation in the world frame: TRANSLATE_R, TRANSLATE_S, ROTATE_R, ROTATE_S

    screwToRasTransform = vtk.vtkTransform()
    screwToRasTransform.Translate(float(parameterNode.GetParameter(self.TRANSLATE_R)),
                                   float(parameterNode.GetParameter(self.TRANSLATE_A)),
                                   float(parameterNode.GetParameter(self.TRANSLATE_S)))
    screwToRasTransform.RotateX(float(parameterNode.GetParameter(self.ROTATE_R)) - 90)  # Start at anterior direction
    screwToRasTransform.RotateY(float(parameterNode.GetParameter(self.ROTATE_S)))

    # Set the transform to the transform node

    screwToRasTransformNode = parameterNode.GetNodeReference(self.SCREW_TO_RAS_TRANSFORM)
    if screwToRasTransformNode is not None:
      screwToRasTransformNode.SetAndObserveTransformToParent(screwToRasTransform)
    else:
      logging.warning("Screw transform not selected yet")

  def updateParameterNodeFromTransform(self):
    """
    Estimate motion parameters from the current transform. This is needed if we want to continue an existing transform
    that has not been selected previously.
    """
    parameterNode = self.getParameterNode()

    screwToRasTransformNode = parameterNode.GetNodeReference(self.SCREW_TO_RAS_TRANSFORM)
    if screwToRasTransformNode is None:
      return

    screwToRasTransform = screwToRasTransformNode.GetTransformToParent()

    screwToRasTranslation = np.array(screwToRasTransform.GetPosition())
    parameterNode.SetParameter(self.TRANSLATE_R, str(screwToRasTranslation[0]))
    parameterNode.SetParameter(self.TRANSLATE_A, str(screwToRasTranslation[1]))
    parameterNode.SetParameter(self.TRANSLATE_S, str(screwToRasTranslation[2]))

    #todo: This does not correctly preserve orientation. We need to figure out how to get rotation values to be compatible
    # with updateTransformFromParameterNode()

    screwToRasOrientation = np.array(screwToRasTransform.GetOrientation())
    parameterNode.SetParameter(self.ROTATE_R, str(screwToRasOrientation[0] + 90))
    parameterNode.SetParameter(self.ROTATE_S, str(screwToRasOrientation[1]))

  def moveScrewIn(self, distance):
    """
    Move selected screw in the "in-out" direction
    """
    # Get the parameter node
    parameterNode = self.getParameterNode()
    # Get the transform node from the parameter node
    screwToRasTransformNode = parameterNode.GetNodeReference(self.SCREW_TO_RAS_TRANSFORM)
    # Get the transform from the transform node
    screwToRasTransform = screwToRasTransformNode.GetTransformToParent()
    # Find distance in terms of R and S
    Translation_Screw = [0, 0, distance]
    # Rotate Translation_Screw to the parent frame
    Translation_RAS = screwToRasTransform.TransformVector(Translation_Screw)
    # Add Translation_RAS to the current translation
    parameterNode.SetParameter(self.TRANSLATE_R, str(float(parameterNode.GetParameter(self.TRANSLATE_R)) + Translation_RAS[0]))
    parameterNode.SetParameter(self.TRANSLATE_A, str(float(parameterNode.GetParameter(self.TRANSLATE_A)) + Translation_RAS[1]))
    parameterNode.SetParameter(self.TRANSLATE_S, str(float(parameterNode.GetParameter(self.TRANSLATE_S)) + Translation_RAS[2]))
    # Update transform from Parameter Node
    self.updateTransformFromParameterNode()

  def saveResults(self):
    ''' 
    Save the results to a file:
    - The scene as a .mrb file

    '''
    # Get the parameter node
    parameterNode = self.getParameterNode()

    # FILENAME FORMAT = [Date]_ScrewPlanner_[userID]_[patientID].mrb
    # Get the date in format MMMDD
    date = time.strftime("%b%d")
    # Get the user ID
    userID = parameterNode.GetParameter(self.USER_ID)
    # Get the patient ID
    patientID = parameterNode.GetParameter(self.PATIENT_ID)
    # Get the file name
    fileName = date + "_ScrewPlanner_" + userID + "_" + patientID + ".mrb"
    
    # Get the Save Directory from slicer settings
    settings = slicer.app.userSettings()
    saveDirectory = settings.value(self.RESULTS_SAVE_DIRECTORY_SETTING)

    print("Save Directory: " + saveDirectory)
    print( "File Name: " + fileName)


    # # Save the ScrewToRasTransform to saveDirectory with fileName
    # slicer.util.saveNode(screwToRasTransformNode, os.path.join(saveDirectory, fileName))

    # Save the current scene to saveDirectory with fileName
    slicer.util.saveScene(os.path.join(saveDirectory, fileName))


  def LoadScrewModel(self, screwFileNameWOExt, transformName):
    """
    Load the screw "screwFileNameWOExt" model from the specified directory and apply the transform "transformName" to it
    """
    t90Node = slicer.util.getFirstNodeByName("RotationT")
    t90NodeName = t90Node.GetName()

    screwName = transformName.split("_")[0]
    previousScrew = slicer.util.getFirstNodeByName(screwName)
    if (previousScrew is not None):
      slicer.mrmlScene.RemoveNode(previousScrew)
    screwFileName = screwFileNameWOExt + ".obj"
    screwNode = self.LoadModelFromFile(screwFileName, [0,0.7251529,0.945098], True)
    rotationT = vtk.vtkTransform()
    rotationT.RotateX(-90)
    rotationT.RotateZ(180)
    t90Node.SetAndObserveTransformToParent(rotationT) 
    self.ApplyTransformToObject(screwNode, t90NodeName)
    screwNode.HardenTransform()
    self.ApplyTransformToObject(screwNode, transformName)
    screwNode.SetName(screwName)
    # set model slice visibility on
    screwNode.GetModelDisplayNode().SetSliceIntersectionVisibility(True)
    return screwNode


  def LoadModelFromFile(self, modelFileName, colorRGB_array, visibility_bool):
    """
		Load the model "modelFileName" from the specified folder. Set its color to colorRGB_array and enable its visibility according to visibility_bool
		"""
    parameterNode = self.getParameterNode()
    modelFilePath = os.path.join(os.path.dirname(__file__), 'Resources/Models')
    
    try:
      node = slicer.util.getNode(modelFileName)
    
    except:
        node = slicer.util.loadModel(os.path.join(modelFilePath, modelFileName))
        node.GetModelDisplayNode().SetColor(colorRGB_array)
        node.GetModelDisplayNode().SetVisibility(visibility_bool)
        #print (modelFileName + ' model loaded')
    return node         
  
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
    self.transform  = self.GetOrCreateTransform(transformName)

    object.SetAndObserveTransformNodeID(self.transform.GetID())
    
    print ('Transform ' + transformName + ' applied to ' + object.GetName())

  def ResliceDriverToScrew(self, transformID):
    """
    Use the "Volume Reslice Driver" module to move the Red and Green slides according to the selected screw position
    """
    #Get the volume reslice logic
    resliceLogic = slicer.modules.volumereslicedriver.logic()

    #Get the red slice node
    redSliceName = "Red"
    redSliceNode = slicer.app.layoutManager().sliceWidget(redSliceName).mrmlSliceNode()
 
    #Set the driver as the volume and the reslice mode as inplane
    resliceLogic.SetDriverForSlice(transformID, redSliceNode)
    resliceLogic.SetModeForSlice(resliceLogic.MODE_INPLANE, redSliceNode)

    #Get the green slice node
    greenSliceName = "Green"
    greenSliceNode = slicer.app.layoutManager().sliceWidget(greenSliceName).mrmlSliceNode()

    #Set the driver as the volume and the reslice mode as transverse
    resliceLogic.SetDriverForSlice(transformID, greenSliceNode)
    resliceLogic.SetModeForSlice(resliceLogic.MODE_INPLANE90, greenSliceNode)
