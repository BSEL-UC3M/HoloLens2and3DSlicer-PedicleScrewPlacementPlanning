// This code was developed by Alicia Pose Díez de la Lastra, from Universidad Carlos III de Madrid
// This script defines some fields of interest that will be associated to every model transferred to 3D Slicer.
// For the screws, it includes information on the model number, name in the local storage and dimensions. 
// The spine and image models also belong to this class. The fields that don't apply to them (such like dimensions) 
// have to be filled too (i.e. "0"), but 3D Slicer won't read them.

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ModelInfo : MonoBehaviour
{
    public string _name;
    public int _number;
    public string _color;
    public string _diameter;
    public string _length;
    public GameObject _gameObject;    
}
