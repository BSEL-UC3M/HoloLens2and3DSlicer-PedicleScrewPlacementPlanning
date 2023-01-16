// This code was developed by Alicia Pose, from Universidad Carlos III de Madrid
// This script creates all the functions associated to the buttons in canvas.
// They are mainly used to Save all the models information in a json file in the local storage of the computer, to load it back later.
// Example of json's structure:
//// {"name":"P001-Spine","parent":"Models","manipulable":false,"pose":[-0.08028563857078552,-0.0906255915760994,-0.3958186209201813,-0.4078744947910309,0.23608827590942384,-0.15394063293933869,0.8684486150741577,2.3911349773406984,2.3911349773406984,2.3911349773406984],"fileName":"D1L1","diameter":"1","length":"1","number":0}
//// {"name":"Screw-1","parent":"P001-Spine","manipulable":false,"pose":[-0.044746238738298419,-0.11679276078939438,-0.009496527723968029,-0.08198198676109314,0.4100800156593323,0.2244398295879364,0.880193293094635,0.9999998211860657,0.9999999403953552,0.9999999403953552],"fileName":"D4.5L40","diameter":"4.5","length":"40","number":1}
//// {"name":"Screw-2","parent":"P001-Spine","manipulable":false,"pose":[0.016604796051979066,-0.12386954575777054,-0.0038179783150553705,0.042550891637802127,-0.531988263130188,-0.26135411858558657,0.8042835593223572,0.9999998211860657,0.9999999403953552,0.9999998807907105],"fileName":"D4.5L30","diameter":"4.5","length":"30","number":2}
//// {"name":"Screw-3","parent":"P001-Spine","manipulable":false,"pose":[-0.0409901961684227,-0.11711480468511582,0.02834322489798069,0.37663352489471438,-0.45378026366233828,0.10137470811605454,0.8012202382087708,0.6472306847572327,0.6472311019897461,0.6472306251525879],"fileName":"D4.5L40","diameter":"4.5","length":"40","number":3}



// First, import some libraries of interest
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.IO;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEditor;
using Microsoft.MixedReality.Toolkit.UI;
using UnityEngine.SceneManagement;

// Define the class CanvasButtons
public class CanvasButtons : MonoBehaviour
{
    int numberOfScrews; // Number of screws in the scene
    [HideInInspector] public GameObject spineGO; // Spine GameObject
    ModelData spineInfo; // Model information of the spineModel
    ModelData screwInfo; // Model information of the screws
    string screwPrefabsPath; // Path to the screw prefabs

    public string fileName = "ModelsData"; // Name of the saving file
    public string userName; // Name of the user performing the experiment
    public string repetitionNumber; // Repetition number of the experiment
    string savingPath; // Path to save the data

    GameObject openIGTLinkConnectScriptHolder; // Holder of the OpenIGTLinkConnect script
    List<ModelInfo> infoToSendArray; // Array of elements that will be sent to 3D Slicer. In our case, the Spine, the image plane and all the screws
    [HideInInspector] public PressableButtons pressableButtonsScript; // Holder of the PressableButtons script
    [HideInInspector] public Material screwFixed_mat; // Material of the screw when it's fixed in the 3D world

    
    void Start()
    {
        // Retrieve infoToSendArray from the OpenIGTLinkConnect script holder
        OpenIGTLinkConnect openIGTLinkConnectScript = GameObject.Find("OpenIGTLinkConnectHandler").GetComponent<OpenIGTLinkConnect>();
        infoToSendArray = openIGTLinkConnectScript.infoToSend;

        pressableButtonsScript = GameObject.Find("Models").GetComponent<PressableButtons>();

        screwPrefabsPath = Path.Combine("Prefabs", "ScrewPrefabs");
    }

    ////////////////////////////////// WIDGET //////////////////////////////////////

    // This function is called whenever the user presses the corresponding button in canvas
    public void OnSaveModelsClick()
    {
        SaveModels();
    }
    
    // This function is called whenever the user presses the corresponding button in canvas
    public void OnLoadModelsClick()
    {
        LoadModels();        
    }
    
    // This function is called whenever the user presses the corresponding button in canvas
    public void OnResetSceneClick()
    {
        ResetScene();
    }

    

    ////////////////////////////////// LOGIC //////////////////////////////////////

    // Load models according to the information of the desired json file. This button pops up an explorer window to select the json file of interest
    void LoadModels()
    {
        // Path with the json files from all the saved scenes
        string loadingPath = EditorUtility.OpenFilePanel("Load Models Data", "", "json");
        // if loading path is empty, return
        if (loadingPath == "")
        {
            return;
        }
        else
        {
            // Destroy preexisting screws in the scene
            DestroyPreexistingScrews();
            // Read the json file
            using StreamReader reader = new StreamReader(loadingPath);
            int numberOfLines = 0;
            // First, count the number of lines
            while (reader.ReadLine() != null)
            {
                numberOfLines++;
            }

            reader.Close();
            // Reread the file knowing its length. Each corresponds to a model
            using StreamReader reader2 = new StreamReader(loadingPath);
            // Create a for loop to read each line
            for (int i = 0; i < numberOfLines; i++)
            {
                // Read line "i"
                string line = reader2.ReadLine();
                ModelData modelInfo = JsonUtility.FromJson<ModelData>(line);

                // If the line contains information about the spine, procceed. Otherwise, go to the next condition (else if (modelInfo.name.StartsWith("Screw")))
                if (modelInfo.name == spineGO.name)
                {
                    // Load the spine 3D model, assign to it the pose specified in the file, and make it modifiable according to the "manipulable" variable
                    GameObject spineModel = GameObject.Find(modelInfo.name);
                    SetPose(modelInfo, spineModel);
                    if (modelInfo.manipulable)
                    {
                        pressableButtonsScript.OnModifySpineClicked();
                    }
                    else
                    {
                        pressableButtonsScript.OnReleaseSpineClicked();
                    }
                    
                }
                // If the line contains information about a screw, procceed
                else if (modelInfo.name.StartsWith("Screw"))
                {
                    // Load the screw from the screwprefabs path and set it as child of modelInfo.parent
                    string screwPath = Path.Combine(screwPrefabsPath, modelInfo.fileName);
                    GameObject screwItem = Resources.Load(screwPath) as GameObject;
                    Transform screwParentTransform = GameObject.Find(modelInfo.parent).transform;
                    GameObject screw_clone = GameObject.Instantiate(screwItem, screwParentTransform) as GameObject;
                    // Add modelinfo to the new screw
                    ModelInfo screw_MI = pressableButtonsScript.AddInfoToModel(screw_clone, modelInfo.number, modelInfo.diameter, modelInfo.length);
                    // Add this screw to the list of elements that will be sent to 3D Slicer
                    infoToSendArray.Add(screw_MI);
                    // Make the screw modifiable according to the "manipulable" variable
                    if (modelInfo.manipulable)
                    {
                        pressableButtonsScript.ModifyScrew(screw_MI._gameObject, true);
                    }
                    else
                    {
                        pressableButtonsScript.ModifyScrew(screw_MI._gameObject, false);
                    }
                    // Set the established pose
                    SetPose(modelInfo, screw_MI._gameObject);
                }
                // If the file contains information about any other model, it is not defined in this script, so nothing would happen
                else
                {
                    Debug.Log("Model not recognized");
                }
                
            }
                
            reader2.Close();
        }
    }

    // Save all the models in the scene
    void SaveModels()
    {
        // Create a file name with the information set in the Inspector
        string finalFileName = CreateFileName(fileName, userName, repetitionNumber);
        savingPath = Path.Combine(Application.persistentDataPath, finalFileName);
        using StreamWriter writer = new StreamWriter(savingPath);
        
        // Get spine's ModelInfo and write it in the json file
        spineInfo = new ModelData(spineGO);
        spineInfo.pose = GetPose(spineGO);
        string spineJson = JsonUtility.ToJson(spineInfo);
        writer.WriteLine(spineJson);

        // Repeat the procedure with all screws in scene
        numberOfScrews = GameObject.FindGameObjectsWithTag("Screw").Length;
        if (numberOfScrews > 0)
        {
            for (int i = 0; i < numberOfScrews; i++)
            {
                string screwName = "Screw-" + (i+1).ToString();
                screwInfo = new ModelData(GameObject.Find(screwName));
                screwInfo.pose = GetPose(GameObject.Find(screwInfo.name));
                string screwJson = JsonUtility.ToJson(screwInfo);
                writer.WriteLine(screwJson);
            }
        }
        writer.Close();
        Debug.Log(savingPath);
    }

    // Get the 10 variables that define all rotations and scales of a model
    float[] GetPose(GameObject go)
    {
        float[] goInfo = new float[10];
        goInfo[0] = go.transform.localPosition.x;
        goInfo[1] = go.transform.localPosition.y;
        goInfo[2] = go.transform.localPosition.z;
        goInfo[3] = go.transform.localRotation.x;
        goInfo[4] = go.transform.localRotation.y;
        goInfo[5] = go.transform.localRotation.z;
        goInfo[6] = go.transform.localRotation.w;
        goInfo[7] = go.transform.localScale.x;
        goInfo[8] = go.transform.localScale.y;
        goInfo[9] = go.transform.localScale.z;

        return goInfo;
    }

    // Set the pose read in the json file to the GameObject go
    void SetPose(ModelData modelInfo, GameObject go)
    {
        go.transform.localPosition = new Vector3(modelInfo.pose[0], modelInfo.pose[1], modelInfo.pose[2]);
        go.transform.localRotation = new Quaternion(modelInfo.pose[3], modelInfo.pose[4], modelInfo.pose[5], modelInfo.pose[6]);
        go.transform.localScale = new Vector3(modelInfo.pose[7], modelInfo.pose[8], modelInfo.pose[9]);
    }

    // Create a file name with the information set in the inspector
    string CreateFileName(string fileName, string userID, string repetitionNumber)
    {
        string currentDate = System.DateTime.Now.ToString("yyyy-MM-dd_hh-mm-ss") + "_";
        string totalFileName = currentDate +"_User"+ userID + "_Rep" + repetitionNumber + "_" + fileName + ".json";
        return totalFileName;
    }
    
    // Destroy all screws in scene
    void DestroyPreexistingScrews()
    {
        GameObject[] preexistingScrews = GameObject.FindGameObjectsWithTag("Screw");
        for (int i = 0; i < preexistingScrews.Length; i++)
        {
            Destroy(preexistingScrews[i]);
        }    
    }
    
    // Restart the scene    
    void ResetScene()
    {
        SceneManager.LoadScene(SceneManager.GetActiveScene().name);
    }



}

// Define the class ModelData, with all relevant information to save and load the models in scene
public class ModelData
{
    public string name;
    public string parent;
    public bool manipulable;
    public float[] pose;
    public string fileName = "0";
    public string diameter = "0";
    public string length = "0";
    public int number = 0;

    

    public ModelData(GameObject go)
    {
        ModelInfo model_MI = go.GetComponent<ModelInfo>();
        name = go.name;
        parent = go.transform.parent.name;
        manipulable = go.GetComponent<ObjectManipulator>().enabled;
        pose = new float[10];
        diameter = model_MI._diameter;
        length = model_MI._length;
        number = model_MI._number;
        fileName = "D" + diameter + "L" + length;
    }
}
