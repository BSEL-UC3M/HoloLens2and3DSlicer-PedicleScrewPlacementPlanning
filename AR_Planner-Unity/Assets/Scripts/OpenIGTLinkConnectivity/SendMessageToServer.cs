// This code is based on the one provided in: https://github.com/franklinwk/OpenIGTLink-Unity
// Modified by Alicia Pose, from Universidad Carlos III de Madrid
// This script defines de structure to send transform messages using the OpenIGTLink communication protocol


using UnityEngine;
using System;
using System.Net;
using System.IO;
using System.Text;
using System.Collections;
using System.Threading;
using System.Collections.Generic;
using UnityEngine.Networking;
using UnityEngine.UI;
using System.Net.Sockets;
using System.Linq;

public class SendMessageToServer : MonoBehaviour
{
    public static void SendTransformMessage(ModelInfo model_InspectorInfo, int scaleMultiplier, CRC64 crcGenerator, string CRC, SocketHandler socketForUnityAndHoloLens)
    {
        ////////////// Get myModel properties
        string modelName = model_InspectorInfo._name;
        GameObject modelGO = model_InspectorInfo._gameObject;
        string modelDiameter = model_InspectorInfo._diameter;
        string modelLength = model_InspectorInfo._length;
        string numberOfScrews = (GameObject.FindGameObjectsWithTag("Screw").Length).ToString();
        string modelNumber = model_InspectorInfo._number.ToString();
        string modelColor = model_InspectorInfo._color;
        string fileName;
        if (modelName.Contains("Screw"))
        {
            fileName = "D" + modelDiameter + "L" + modelLength + ".obj"; // Name of the file to be loaded in Slicer
        }
        else 
        {
            fileName = "None";
        }
        

        /////// HEADER INFORMATION:
        // Version 2
        // Type Transform
        // Device Name 
        // Time 0
        // Body size 30 bytes
        // EXAMPLE: 0002 Type:5452414E53464F524D000000 Name:4F63756C757352696674506F736974696F6E0000 00000000000000000000000000000030
        
        // Define Header in hexadecimal
        string deviceName = modelName + "_T";

        // Define the version in hexadecimal
        string oigtlVersion = "0002";
        
        
        // Elements of the matrix
        string m00Hex;
        string m01Hex;
        string m02Hex;
        string m03Hex;
        string m10Hex;
        string m11Hex;
        string m12Hex;
        string m13Hex;
        string m20Hex;
        string m21Hex;
        string m22Hex;
        string m23Hex;

        // Get rotation of myOBJ and add a minus (-) sign to x axis to convert from Unity to Slicer coordinate system
        var myOBJRotation = modelGO.transform.localRotation.eulerAngles;
        var adaptedRotationFromDeviceToSlicer = new Vector3(-myOBJRotation.x, myOBJRotation.y, -myOBJRotation.z);
        var rotationForSlicer = Quaternion.Euler(adaptedRotationFromDeviceToSlicer);

        // Obtain a 4x4 matrix with all the pose information of myOBJ, including the minus (-) sign in the x axis of rotation
        Matrix4x4 matrix = Matrix4x4.TRS(modelGO.transform.localPosition, rotationForSlicer, modelGO.transform.localScale);

        float m00 = matrix.GetRow(0)[0];
        byte[] m00Bytes = BitConverter.GetBytes(m00);
        float m01 = matrix.GetRow(0)[1];
        byte[] m01Bytes = BitConverter.GetBytes(m01);
        float m02 = matrix.GetRow(0)[2];
        byte[] m02Bytes = BitConverter.GetBytes(m02);
        float m03 = matrix.GetRow(0)[3];                    
        byte[] m03Bytes = BitConverter.GetBytes(m03 * scaleMultiplier);

        float m10 = matrix.GetRow(1)[0];
        byte[] m10Bytes = BitConverter.GetBytes(m10);
        float m11 = matrix.GetRow(1)[1];
        byte[] m11Bytes = BitConverter.GetBytes(m11);
        float m12 = matrix.GetRow(1)[2];
        byte[] m12Bytes = BitConverter.GetBytes(m12);
        float m13 = -matrix.GetRow(1)[3];                   // (-) because of Unity coordinate system
        byte[] m13Bytes = BitConverter.GetBytes(m13 * scaleMultiplier);

        float m20 = matrix.GetRow(2)[0];
        byte[] m20Bytes = BitConverter.GetBytes(m20);
        float m21 = matrix.GetRow(2)[1];
        byte[] m21Bytes = BitConverter.GetBytes(m21);
        float m22 = matrix.GetRow(2)[2];
        byte[] m22Bytes = BitConverter.GetBytes(m22);
        float m23 = matrix.GetRow(2)[3];
        byte[] m23Bytes = BitConverter.GetBytes(m23 * scaleMultiplier);

        // If little endian, reverse the bytes
        if (BitConverter.IsLittleEndian)
        {
            Array.Reverse(m00Bytes);
            Array.Reverse(m01Bytes);
            Array.Reverse(m02Bytes);
            Array.Reverse(m03Bytes);
            Array.Reverse(m10Bytes);
            Array.Reverse(m11Bytes);
            Array.Reverse(m12Bytes);
            Array.Reverse(m13Bytes);
            Array.Reverse(m20Bytes);
            Array.Reverse(m21Bytes);
            Array.Reverse(m22Bytes);
            Array.Reverse(m23Bytes);
        }

        // Convert bytes to hexadecimal
        m00Hex = BitConverter.ToString(m00Bytes).Replace("-", "");
        m01Hex = BitConverter.ToString(m01Bytes).Replace("-", "");
        m02Hex = BitConverter.ToString(m02Bytes).Replace("-", "");
        m03Hex = BitConverter.ToString(m03Bytes).Replace("-", "");
        m10Hex = BitConverter.ToString(m10Bytes).Replace("-", "");
        m11Hex = BitConverter.ToString(m11Bytes).Replace("-", "");
        m12Hex = BitConverter.ToString(m12Bytes).Replace("-", "");
        m13Hex = BitConverter.ToString(m13Bytes).Replace("-", "");
        m20Hex = BitConverter.ToString(m20Bytes).Replace("-", "");
        m21Hex = BitConverter.ToString(m21Bytes).Replace("-", "");
        m22Hex = BitConverter.ToString(m22Bytes).Replace("-", "");
        m23Hex = BitConverter.ToString(m23Bytes).Replace("-", "");

        // Create string with all the matrix elements
        string body = m00Hex + m10Hex + m20Hex + m01Hex + m11Hex + m21Hex + m02Hex + m12Hex + m22Hex + m03Hex + m13Hex + m23Hex;

        
        /////// EXTENDED HEADER INFORMATION:
        // EXT_HEADER_SIZE: UInt16. Size of the Extended Header: Always 12 in OpenIGTLink communications
        // METADATA_HEADER_SIZE: UInt16 that represents the length of your Metadata 
        // METADATA_SIZE: Uint16. Variable size depending on the number of attributes contained in the metadata
        // MSG_ID: UInt32. ID of your message. Not important for us. Let's just write 0.


        /////// META DATA INFORMATION:
        ///// META DATA HEADER:
        // INDEX_COUNT: UInt16 with the number of attributes we want to send in the meta data.
        // Metadata 0
        // Metadata 1
        // [...]
        /// Metadata X architecture:
        // KEY_SIZE: UInt16. Size of the key X in bytes
        // VALUE_ENCODING: UInt16. Character encoding type for value as MIBenum value. Default 3 for US-ASCII
        // VALUE_SIZE: UInt32. Size of value X in bytes

        //// METADATA BODY:
        // Metadata X:
        // KEY: UInt16. The key itself. It's size should be the one stored in KEY_SIZE_X
        // VALUE: UInt16. The value itself. It's size should be the one stored in VALUE_SIZE_X. It should be encoded according to VALUE_ENCODING

        ///// In the following lines we are going to take every variable and convert it into the variable type
        ///// requested in the OpenIGTLink protocol. Then, we will convert this variable into a byte[]
        ///// and the byte[] into a hexadecimal string. We can't convert byte[], so we convert those
        ///// to strings that can be easily concatenated. For the final message, we will convert the 
        ///// hexadecimal string into a byte[] again.

        // Create Metadata information
        string[] md_keyNames = {"ModelName", "ModelColor", "ModelNumber", "NumOfScrews"};
        string[] md_keyValues = {fileName, modelColor, modelNumber, numberOfScrews};

        // Get VALUE_ENCODING
        UInt16 encodingValue_UINT16 = Convert.ToUInt16(3);
        byte[] value_encoding_BYTES = BitConverter.GetBytes(encodingValue_UINT16);
        if (BitConverter.IsLittleEndian)
        {
            Array.Reverse(value_encoding_BYTES);
        }
        string VALUE_ENCODING = BitConverter.ToString(value_encoding_BYTES).Replace("-", "");
        


        // Create META_HEADER and META_DATA
        string META_HEADER = "";
        string META_DATA = "";
        for (int index = 0; index < md_keyNames.Length; index++)
        {
            //Debug.Log("Key: " + md_keyNames[index] + " Value: " + md_keyValues[index]);
            byte[] currentKey_BYTES = Encoding.ASCII.GetBytes(md_keyNames[index]);
            byte[] currentValue_BYTES = Encoding.ASCII.GetBytes(md_keyValues[index]);

            ///////////// Build META_HEADER
            // Convert values to the corresponding variable type
            UInt16 currentValueLength_UINT16 = Convert.ToUInt16(currentKey_BYTES.Length);
            UInt32 currentValueLength_UINT32 = Convert.ToUInt16(currentValue_BYTES.Length);
            // Convert these variables into byte[]
            byte[] key_size_BYTES = BitConverter.GetBytes(currentValueLength_UINT16);
            byte[] value_size_BYTES = BitConverter.GetBytes(currentValueLength_UINT32);
            if (BitConverter.IsLittleEndian)
            {
                Array.Reverse(key_size_BYTES);
                Array.Reverse(value_size_BYTES);
            }
            // Convert the byte[] into hexadecimal strings
            string KEY_SIZE = BitConverter.ToString(key_size_BYTES).Replace("-", "");
            string VALUE_SIZE = BitConverter.ToString(value_size_BYTES).Replace("-", "");
            // Concatenate the strings to form the metaheader
            META_HEADER += KEY_SIZE + VALUE_ENCODING + VALUE_SIZE;

            ///////////// Build META_DATA
            // Convert the byte[] into hexadecimal strings
            string KEY = BitConverter.ToString(currentKey_BYTES).Replace("-", "");
            string VALUE = BitConverter.ToString(currentValue_BYTES).Replace("-", "");
            // Concatenate the strings to form the metaheader
            META_DATA += KEY + VALUE;
        }

        // Get INDEX_COUNT
        UInt16 countIndexes_UINT16 = Convert.ToUInt16(md_keyNames.Count()); // Number of meta data
        byte[] index_count_BYTES = BitConverter.GetBytes(countIndexes_UINT16);
        if (BitConverter.IsLittleEndian)
        {
            Array.Reverse(index_count_BYTES);
        }
        string INDEX_COUNT = BitConverter.ToString(index_count_BYTES).Replace("-", "");

        // Complete the metadata information
        string hexMetaBody = INDEX_COUNT + META_HEADER + META_DATA; // Create Metadata body in hexadecimal. It starts with INDEX_COUNT and then grows  with the metaheaders and meta data



        ///////////// Build EXTENDED HEADER
        // Convert values to the corresponding variable type
        UInt16 extHeaderSize_UINT16 = Convert.ToUInt16(12);
        UInt16 metadataHeaderSize_UINT16 = Convert.ToUInt16((INDEX_COUNT.Length + META_HEADER.Length) / 2);
        UInt32 metadataSize_UINT32 = Convert.ToUInt32(META_DATA.Length / 2);
        UInt32 msgID_UINT32 = Convert.ToUInt32(0);

        // Convert these variables into byte[]
        byte[] extHeaderSize_BYTES = BitConverter.GetBytes(extHeaderSize_UINT16);
        byte[] metadataHeaderSize_BYTES = BitConverter.GetBytes(metadataHeaderSize_UINT16);
        byte[] metadataSize_BYTES = BitConverter.GetBytes(metadataSize_UINT32);
        byte[] msgID_BYTES = BitConverter.GetBytes(msgID_UINT32);
        if (BitConverter.IsLittleEndian)
        {
            Array.Reverse(extHeaderSize_BYTES);
            Array.Reverse(metadataHeaderSize_BYTES);
            Array.Reverse(metadataSize_BYTES);
            Array.Reverse(msgID_BYTES);
        }
        // Convert the byte[] into hexadecimal strings
        string EXT_HEADER_SIZE = BitConverter.ToString(extHeaderSize_BYTES).Replace("-", "");
        string METADATA_HEADER_SIZE = BitConverter.ToString(metadataHeaderSize_BYTES).Replace("-", "");
        string METADATA_SIZE = BitConverter.ToString(metadataSize_BYTES).Replace("-", "");
        string MSG_ID = BitConverter.ToString(msgID_BYTES).Replace("-", "");

        // Create final extended header
        string hexExtHeader = EXT_HEADER_SIZE + METADATA_HEADER_SIZE + METADATA_SIZE + MSG_ID;
        

        //string deviceName = "Screw-" + myScrew._number + "_T";
        string timeStamp = BitConverter.ToString(BitConverter.GetBytes(Convert.ToUInt64(0))).Replace("-", "");
        string bodySize = ((hexExtHeader + body + hexMetaBody).Length / 2).ToString("X16");
        string hexHeader = oigtlVersion + StringToHexString("TRANSFORM", 12) + StringToHexString(deviceName, 20) + timeStamp + bodySize;

        // Calculate CRC
        // Obtain the CRC associated to this message
        ulong crcULong = crcGenerator.Compute(StringToByteArray(hexExtHeader + body + hexMetaBody), 0, 0);
        CRC = crcULong.ToString("X16");

        // Combine all the information to send
        string hexmsg = hexHeader + CRC + hexExtHeader + body + hexMetaBody;

        // Encode the data string into a byte array.
        byte[] msg = SendMessageToServer.StringToByteArray(hexmsg);
        
        // Send the data through the socket.     
        socketForUnityAndHoloLens.Send(msg);
    }

    // --- Send Helpers ---
    public static string StringToHexString(string inputString, int sizeInBytes)
    {
        if (inputString.Length > sizeInBytes)
        {
            inputString = inputString.Substring(0, sizeInBytes);
        }

        byte[] ba = Encoding.Default.GetBytes(inputString);
        string hexString = BitConverter.ToString(ba);
        hexString = hexString.Replace("-", "");
        hexString = hexString.PadRight(sizeInBytes * 2, '0');
        return hexString;
    }

    public static byte[] StringToByteArray(string hex)
    {
        byte[] arr = new byte[hex.Length >> 1];

        for (int i = 0; i < (hex.Length >> 1); ++i)
        {
            arr[i] = (byte)((GetHexVal(hex[i << 1]) << 4) + (GetHexVal(hex[(i << 1) + 1])));
        }

        return arr;
    }
    
    static int GetHexVal(char hex)
    {
        int val = (int)hex;
        //For uppercase:
        return val - (val < 58 ? 48 : 55);
        //For lowercase:
        //return val - (val < 58 ? 48 : 87);
    }
}
