// This code was developed by Alicia Pose Díez de la Lastra, from Universidad Carlos III de Madrid
// This script scales of the 3D biomodels in the scene according to the spine scale

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ModelScaling : MonoBehaviour
{
    // Start is called before the first frame update
    [HideInInspector] public GameObject spineModel; // Spine model
    [HideInInspector] public Transform modelsParent; // Models parent
    Vector3 previousSpineScale; // Spine scale the last time it was modified
    Vector3 currentSpineScale; // New spine scale
    
    void Start()
    {
        previousSpineScale = Vector3.zero; // Define previousSpineScale to a vector of zeros
    }

    // Update is called once per frame
    void Update()
    {
        currentSpineScale = spineModel.transform.localScale; // Get the current spine scale
        if (currentSpineScale != previousSpineScale) // If it differs from the previous register, continue
        {
            foreach (Transform model in modelsParent) // Update the scale of every model in the models parent transform
            {
                model.localScale = currentSpineScale;
            }
            previousSpineScale = currentSpineScale; // Update the previousSpineScale variable
        }
        
    }
}
