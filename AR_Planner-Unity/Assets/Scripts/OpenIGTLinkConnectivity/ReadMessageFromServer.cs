// This code is based on the one provided in: https://github.com/franklinwk/OpenIGTLink-Unity
// Modified by Alicia Pose, from Universidad Carlos III de Madrid
// This script defines de structure to read transform and image messages using the OpenIGTLink communication protocol

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

public class ReadMessageFromServer
{
    // Information to send the transform
    static Matrix4x4 matrix = new Matrix4x4();
    
    //////////////////////////////// READING INCOMING MESSAGE ////////////////////////////////
    /// Define structure of the incoming message's header ///
    public struct HeaderInfo
    {
        public uint headerSize;
        public UInt16 versionNumber;
        public string msgType;
        public string deviceName;
        public UInt64 timestamp;
        public UInt64 bodySize;
        public UInt64 crc64;
        public UInt16 extHeaderSize;
    }
    /// Read incoming message's header ///
    public static HeaderInfo ReadHeaderInfo(byte[] iMSGbyteArray)
    {
        // Define the size of each of the components of the header 
        // according to the the OpenIGTLink protocol
        // See documentation: https://github.com/openigtlink/OpenIGTLink/blob/master/Documents/Protocol/header.md
        byte[] byteArray_Version = new byte[2];
        byte[] byteArray_MsgType = new byte[12];
        byte[] byteArray_DeviceName = new byte[20];
        byte[] byteArray_TimeStamp = new byte[8];
        byte[] byteArray_BodySize = new byte[8];
        byte[] byteArray_CRC = new byte[8];
        byte[] byteArray_ExtHeaderSize = new byte[2];

        // Define the offset to skip in the reader to reach the next variable (SP = starting point)
        int version_SP = 0;
        int msgType_SP = version_SP + byteArray_Version.Length;
        int deviceName_SP = msgType_SP + byteArray_MsgType.Length;
        int timeStamp_SP = deviceName_SP + byteArray_DeviceName.Length;
        int bodySize_SP = timeStamp_SP + byteArray_TimeStamp.Length;
        int crc_SP = bodySize_SP + byteArray_BodySize.Length;
        int extHeaderSize_SP = crc_SP + byteArray_CRC.Length;
        

        // Store the information into the variables
        Buffer.BlockCopy(iMSGbyteArray, version_SP, byteArray_Version, 0, byteArray_Version.Length);
        Buffer.BlockCopy(iMSGbyteArray, msgType_SP, byteArray_MsgType, 0, byteArray_MsgType.Length);
        Buffer.BlockCopy(iMSGbyteArray, deviceName_SP, byteArray_DeviceName, 0, byteArray_DeviceName.Length);
        Buffer.BlockCopy(iMSGbyteArray, timeStamp_SP, byteArray_TimeStamp, 0, byteArray_TimeStamp.Length);
        Buffer.BlockCopy(iMSGbyteArray, bodySize_SP, byteArray_BodySize, 0, byteArray_BodySize.Length);
        Buffer.BlockCopy(iMSGbyteArray, crc_SP, byteArray_CRC, 0, byteArray_CRC.Length);
        Buffer.BlockCopy(iMSGbyteArray, extHeaderSize_SP, byteArray_ExtHeaderSize, 0, byteArray_ExtHeaderSize.Length);


        // If the message is Little Endian, convert it to Big Endian
        if (BitConverter.IsLittleEndian)
        {
            Array.Reverse(byteArray_Version);
            //Array.Reverse(byteArray_MsgType);     // No need to reverse strings
            //Array.Reverse(byteArray_DeviceName);  // No need to reverse strings
            Array.Reverse(byteArray_TimeStamp);
            Array.Reverse(byteArray_BodySize);
            Array.Reverse(byteArray_CRC);
            Array.Reverse(byteArray_ExtHeaderSize);
        }

        // Convert the byte arrays to the corresponding data type
        UInt16 versionNumber_iMSG = BitConverter.ToUInt16(byteArray_Version);
        string msgType_iMSG = Encoding.ASCII.GetString(byteArray_MsgType);
        string deviceName_iMSG = Encoding.ASCII.GetString(byteArray_DeviceName);
        UInt64 timestamp_iMSG = BitConverter.ToUInt64(byteArray_TimeStamp);
        UInt64 bodySize_iMSG = BitConverter.ToUInt64(byteArray_BodySize);
        UInt64 crc_iMSG = BitConverter.ToUInt64(byteArray_CRC);
        UInt16 extHeaderSize_iMSG = BitConverter.ToUInt16(byteArray_ExtHeaderSize);

        
        // Store all this values in the HeaderInfo structure
        HeaderInfo incomingHeaderInfo = new HeaderInfo();
        incomingHeaderInfo.headerSize = 58;
        incomingHeaderInfo.versionNumber = versionNumber_iMSG;
        incomingHeaderInfo.msgType = msgType_iMSG;
        incomingHeaderInfo.deviceName = deviceName_iMSG;
        incomingHeaderInfo.timestamp = timestamp_iMSG;
        incomingHeaderInfo.bodySize = bodySize_iMSG;
        incomingHeaderInfo.crc64 = crc_iMSG;
        incomingHeaderInfo.extHeaderSize = extHeaderSize_iMSG;

        return incomingHeaderInfo;
    }
    
    /// Define structure of the incoming image information ///
    public struct ImageInfo
    {
        public UInt16 versionNumber;
        public int imComp;
        public int scalarType;
        public int endian;
        public int imCoord;
        public UInt16 numPixX;
        public UInt16 numPixY;
        public UInt16 numPixZ;
        public float xi;
        public float yi;
        public float zi;
        public float xj;
        public float yj;
        public float zj;
        public float xk;
        public float yk;
        public float zk;
        public float centerPosX;
        public float centerPosY;
        public float centerPosZ;
        public UInt16 startingIndexSVX;
        public UInt16 startingIndexSVY;
        public UInt16 startingIndexSVZ;
        public UInt16 numPixSVX;
        public UInt16 numPixSVY;
        public UInt16 numPixSVZ;
        public int offsetBeforeImageContent;
    }
    
    /// Read incoming image's information ///
    public static ImageInfo ReadImageInfo(byte[] iMSGbyteArrayComplete, uint headerSize, UInt16 extHeaderSize_iMSG)
    {
        // Define the variables stored in the body of the message
        int[] bodyArrayLengths = new int[]{2, 1, 1, 1, 1, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2, 2, 2};
        
        ImageInfo incomingImageInfo = new ImageInfo();

        int skipTheseBytes = (int)headerSize + (int)extHeaderSize_iMSG - 2;
        for (int index = 0; index < bodyArrayLengths.Length; index++)
        {
            byte[] sectionByteArray = new byte[bodyArrayLengths[index]];
            skipTheseBytes = skipTheseBytes + bodyArrayLengths[index];
            Buffer.BlockCopy(iMSGbyteArrayComplete, skipTheseBytes, sectionByteArray, 0, bodyArrayLengths[index]);
            if (BitConverter.IsLittleEndian)
            {
                Array.Reverse(sectionByteArray);
            }

            switch (index)
            {
                case 0: 
                    UInt16 versionNumber_bodyIm = BitConverter.ToUInt16(sectionByteArray);
                    incomingImageInfo.versionNumber = versionNumber_bodyIm; break;
                case 1:
                    byte[] bodyArray_ImComp = sectionByteArray;
                    incomingImageInfo.imComp = bodyArray_ImComp[0]; break;
                case 2: 
                    byte[] bodyArray_scalarType = sectionByteArray;
                    incomingImageInfo.scalarType = bodyArray_scalarType[0]; break;
                case 3:
                    byte[] bodyArray_Endian = sectionByteArray;
                    incomingImageInfo.endian = bodyArray_Endian[0]; break;
                case 4:
                    byte[] bodyArray_ImCoord = sectionByteArray;
                    incomingImageInfo.imCoord = bodyArray_ImCoord[0]; break;
                case 5:
                    UInt16 numPixX_bodyIm = BitConverter.ToUInt16(sectionByteArray);
                    incomingImageInfo.numPixX = numPixX_bodyIm; break;
                case 6:
                    UInt16 numPixY_bodyIm = BitConverter.ToUInt16(sectionByteArray);
                    incomingImageInfo.numPixY = numPixY_bodyIm; break;
                case 7:
                    UInt16 numPixZ_bodyIm = BitConverter.ToUInt16(sectionByteArray);
                    incomingImageInfo.numPixZ = numPixZ_bodyIm; break;
                case 8:
                    float xi_bodyIm = BitConverter.ToUInt16(sectionByteArray);
                    incomingImageInfo.xi = xi_bodyIm; break;
                case 9:
                    float yi_bodyIm = BitConverter.ToUInt16(sectionByteArray);
                    incomingImageInfo.yi = yi_bodyIm; break;
                case 10:
                    float zi_bodyIm = BitConverter.ToUInt16(sectionByteArray);
                    incomingImageInfo.zi = zi_bodyIm; break;
                case 11:
                    float xj_bodyIm = BitConverter.ToUInt16(sectionByteArray);
                    incomingImageInfo.xj = xj_bodyIm; break;
                case 12:
                    float yj_bodyIm = BitConverter.ToSingle(sectionByteArray, 0);
                    incomingImageInfo.yj = yj_bodyIm; break;
                case 13:
                    float zj_bodyIm = BitConverter.ToSingle(sectionByteArray, 0);
                    incomingImageInfo.zj = zj_bodyIm; break;
                case 14:
                    float xk_bodyIm = BitConverter.ToSingle(sectionByteArray, 0);
                    incomingImageInfo.xk = xk_bodyIm; break;
                case 15:
                    float yk_bodyIm = BitConverter.ToSingle(sectionByteArray, 0);
                    incomingImageInfo.yj = yk_bodyIm; break;
                case 16:
                    float zk_bodyIm = BitConverter.ToSingle(sectionByteArray, 0);
                    incomingImageInfo.zj = zk_bodyIm; break;
                case 17:
                    float centerPosX_bodyIm = BitConverter.ToSingle(sectionByteArray, 0);
                    incomingImageInfo.centerPosX = centerPosX_bodyIm; break;
                case 18:
                    float centerPosY_bodyIm = BitConverter.ToSingle(sectionByteArray, 0);
                    incomingImageInfo.centerPosY = centerPosY_bodyIm; break;
                case 19:
                    float centerPosZ_bodyIm = BitConverter.ToSingle(sectionByteArray, 0);
                    incomingImageInfo.centerPosZ = centerPosZ_bodyIm; break;
                case 20:
                    UInt16 startingIndexSVX_bodyIm = BitConverter.ToUInt16(sectionByteArray, 0);
                    incomingImageInfo.startingIndexSVX = startingIndexSVX_bodyIm; break;
                case 21:
                    UInt16 startingIndexSVY_bodyIm = BitConverter.ToUInt16(sectionByteArray, 0);
                    incomingImageInfo.startingIndexSVY = startingIndexSVY_bodyIm; break;
                case 22:
                    UInt16 startingIndexSVZ_bodyIm = BitConverter.ToUInt16(sectionByteArray, 0);
                    incomingImageInfo.startingIndexSVZ = startingIndexSVZ_bodyIm; break;
                case 23:
                    UInt16 numPixSVX_bodyIm = BitConverter.ToUInt16(sectionByteArray, 0);
                    incomingImageInfo.numPixSVX = numPixSVX_bodyIm; break;
                case 24:
                    UInt16 numPixSVY_bodyIm = BitConverter.ToUInt16(sectionByteArray, 0);
                    incomingImageInfo.numPixSVY = numPixSVY_bodyIm; break;
                case 25:
                    UInt16 numPixSVZ_bodyIm = BitConverter.ToUInt16(sectionByteArray, 0);
                    incomingImageInfo.numPixSVZ = numPixSVZ_bodyIm; break;
                default:
                    break;
                
            }
        }
        
        int offsetBeforeImageContent = skipTheseBytes;
        incomingImageInfo.offsetBeforeImageContent = offsetBeforeImageContent;
        
        return incomingImageInfo;
    }


    //////////////////////////////// INCOMING TRANSFORM MESSAGE ////////////////////////////////
    /// Extract transform information ///
    public static Matrix4x4 ExtractTransformInfo(byte[] iMSGbyteArray, GameObject go, int scaleMultiplier, int headerSize)
    {
        byte[] matrixBytes = new byte[4];
        float[] m = new float[16];
        for (int i = 0; i < 16; i++)
        { 
            Buffer.BlockCopy(iMSGbyteArray, (int)headerSize + 12 + i * 4, matrixBytes, 0, 4); // We add +12 to skip the extended header
            if (BitConverter.IsLittleEndian)
            {
                Array.Reverse(matrixBytes);
            }

            m[i] = BitConverter.ToSingle(matrixBytes, 0);
            
        }
        
        matrix.SetRow(0, new Vector4(m[0], m[3], m[6], m[9] / scaleMultiplier));
        matrix.SetRow(1, new Vector4(m[1], m[4], m[7], m[10] / scaleMultiplier));
        matrix.SetRow(2, new Vector4(m[2], m[5], m[8], m[11] / scaleMultiplier));
        matrix.SetRow(3, new Vector4(0.0f, 0.0f, 0.0f, 1.0f));
        
        return matrix;
    }
}
