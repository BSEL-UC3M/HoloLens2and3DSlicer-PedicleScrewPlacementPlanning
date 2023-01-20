// This code was developed by Alicia Pose Díez de la Lastra, from Universidad Carlos III de Madrid
// This script associates the clipping plane material with the image plane gameobject

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ClippingPlane : MonoBehaviour
{
    public Material clipping_mat; // Clipping plane material
    
    //execute every frame
    void Update () 
    {
        //create plane
        Plane plane = new Plane(transform.up, transform.position);
        //transfer values from plane to vector4
        Vector4 planeRepresentation = new Vector4(plane.normal.x, plane.normal.y, plane.normal.z, plane.distance);
        //pass vector to shader
        clipping_mat.SetVector("_Plane", planeRepresentation);
    }
}
