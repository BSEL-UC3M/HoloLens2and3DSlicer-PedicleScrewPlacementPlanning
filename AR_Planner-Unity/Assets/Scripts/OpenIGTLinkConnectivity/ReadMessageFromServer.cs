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
        byte[] bodyArray_Version = new byte[2];
        byte[] bodyArray_ImComp = new byte[1];
        byte[] bodyArray_ScalarType = new byte[1];
        byte[] bodyArray_Endian = new byte[1];
        byte[] bodyArray_ImCoord = new byte[1];
        byte[] bodyArray_NumPixX = new byte[2];
        byte[] bodyArray_NumPixY = new byte[2];
        byte[] bodyArray_NumPixZ = new byte[2];
        byte[] bodyArray_Xi = new byte[4];
        byte[] bodyArray_Yi = new byte[4];
        byte[] bodyArray_Zi = new byte[4];
        byte[] bodyArray_Xj = new byte[4];
        byte[] bodyArray_Yj = new byte[4];
        byte[] bodyArray_Zj = new byte[4];
        byte[] bodyArray_Xk = new byte[4];
        byte[] bodyArray_Yk = new byte[4];
        byte[] bodyArray_Zk = new byte[4];
        byte[] bodyArray_CenterPosX = new byte[4];
        byte[] bodyArray_CenterPosY = new byte[4];
        byte[] bodyArray_CenterPosZ = new byte[4];
        byte[] bodyArray_StartingIndexSVX = new byte[2];
        byte[] bodyArray_StartingIndexSVY = new byte[2];
        byte[] bodyArray_StartingIndexSVZ = new byte[2];
        byte[] bodyArray_NumPixSVX = new byte[2];
        byte[] bodyArray_NumPixSVY = new byte[2];
        byte[] bodyArray_NumPixSVZ = new byte[2];

        // Define the offset to skip in the reader to reach the next variable (SP = starting point)
        int version_SP = (int)headerSize + (int)extHeaderSize_iMSG;
        int imComp_SP = version_SP + bodyArray_Version.Length;
        int scalarType_SP = imComp_SP + bodyArray_ImComp.Length;
        int endian_SP = scalarType_SP + bodyArray_ScalarType.Length;
        int imCoord_SP = endian_SP + bodyArray_Endian.Length;
        int numPixX_SP = imCoord_SP + bodyArray_ImCoord.Length;
        int numPixY_SP = numPixX_SP + bodyArray_NumPixX.Length;
        int numPixZ_SP = numPixY_SP + bodyArray_NumPixY.Length;
        int xi_SP = numPixZ_SP + bodyArray_NumPixZ.Length;
        int yi_SP = xi_SP + bodyArray_Xi.Length;
        int zi_SP = yi_SP + bodyArray_Yi.Length;
        int xj_SP = zi_SP + bodyArray_Zi.Length;
        int yj_SP = xj_SP + bodyArray_Xj.Length;
        int zj_SP = yj_SP + bodyArray_Yj.Length;
        int xk_SP = zj_SP + bodyArray_Zj.Length;
        int yk_SP = xk_SP + bodyArray_Xk.Length;
        int zk_SP = yk_SP + bodyArray_Yk.Length;
        int centerPosX_SP = zk_SP + bodyArray_Zk.Length;
        int centerPosY_SP = centerPosX_SP + bodyArray_CenterPosX.Length;
        int centerPosZ_SP = centerPosY_SP + bodyArray_CenterPosY.Length;
        int startingIndexSVX_SP = centerPosZ_SP + bodyArray_CenterPosZ.Length;
        int startingIndexSVY_SP = startingIndexSVX_SP + bodyArray_StartingIndexSVX.Length;
        int startingIndexSVZ_SP = startingIndexSVY_SP + bodyArray_StartingIndexSVY.Length;
        int numPixSVX_SP = startingIndexSVZ_SP + bodyArray_StartingIndexSVZ.Length;
        int numPixSVY_SP = numPixSVX_SP + bodyArray_NumPixSVX.Length;
        int numPixSVZ_SP = numPixSVY_SP + bodyArray_NumPixSVY.Length;


        // Store the information into the variables
        Buffer.BlockCopy(iMSGbyteArrayComplete, version_SP, bodyArray_Version, 0, bodyArray_Version.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, imComp_SP, bodyArray_ImComp, 0, bodyArray_ImComp.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, scalarType_SP, bodyArray_ScalarType, 0, bodyArray_ScalarType.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, endian_SP, bodyArray_Endian, 0, bodyArray_Endian.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, imCoord_SP, bodyArray_ImCoord, 0, bodyArray_ImCoord.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, numPixX_SP, bodyArray_NumPixX, 0, bodyArray_NumPixX.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, numPixY_SP, bodyArray_NumPixY, 0, bodyArray_NumPixY.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, numPixZ_SP, bodyArray_NumPixZ, 0, bodyArray_NumPixZ.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, xi_SP, bodyArray_Xi, 0, bodyArray_Xi.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, yi_SP, bodyArray_Yi, 0, bodyArray_Yi.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, zi_SP, bodyArray_Zi, 0, bodyArray_Zi.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, xj_SP, bodyArray_Xj, 0, bodyArray_Xj.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, yj_SP, bodyArray_Yj, 0, bodyArray_Yj.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, zj_SP, bodyArray_Zj, 0, bodyArray_Zj.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, xk_SP, bodyArray_Xk, 0, bodyArray_Xk.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, yk_SP, bodyArray_Yk, 0, bodyArray_Yk.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, zk_SP, bodyArray_Zk, 0, bodyArray_Zk.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, centerPosX_SP, bodyArray_CenterPosX, 0, bodyArray_CenterPosX.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, centerPosY_SP, bodyArray_CenterPosY, 0, bodyArray_CenterPosY.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, centerPosZ_SP, bodyArray_CenterPosZ, 0, bodyArray_CenterPosZ.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, startingIndexSVX_SP, bodyArray_StartingIndexSVX, 0, bodyArray_StartingIndexSVX.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, startingIndexSVY_SP, bodyArray_StartingIndexSVY, 0, bodyArray_StartingIndexSVY.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, startingIndexSVZ_SP, bodyArray_StartingIndexSVZ, 0, bodyArray_StartingIndexSVZ.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, numPixSVX_SP, bodyArray_NumPixSVX, 0, bodyArray_NumPixSVX.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, numPixSVY_SP, bodyArray_NumPixSVY, 0, bodyArray_NumPixSVY.Length);
        Buffer.BlockCopy(iMSGbyteArrayComplete, numPixSVZ_SP, bodyArray_NumPixSVZ, 0, bodyArray_NumPixSVZ.Length);

        int offsetBeforeImageContent = numPixSVZ_SP + bodyArray_NumPixSVZ.Length;

        // If the message is Little Endiant, reverse the contents of the arrays
        if (BitConverter.IsLittleEndian)
        {
            Array.Reverse(bodyArray_Version);
            Array.Reverse(bodyArray_ImComp);
            Array.Reverse(bodyArray_ScalarType);
            Array.Reverse(bodyArray_Endian);
            Array.Reverse(bodyArray_ImCoord);
            Array.Reverse(bodyArray_NumPixX);
            Array.Reverse(bodyArray_NumPixY);
            Array.Reverse(bodyArray_NumPixZ);
            Array.Reverse(bodyArray_Xi);
            Array.Reverse(bodyArray_Yi);
            Array.Reverse(bodyArray_Zi);
            Array.Reverse(bodyArray_Xj);
            Array.Reverse(bodyArray_Yj);
            Array.Reverse(bodyArray_Zj);
            Array.Reverse(bodyArray_Xk);
            Array.Reverse(bodyArray_Yk);
            Array.Reverse(bodyArray_Zk);
            Array.Reverse(bodyArray_CenterPosX);
            Array.Reverse(bodyArray_CenterPosY);
            Array.Reverse(bodyArray_CenterPosZ);
            Array.Reverse(bodyArray_StartingIndexSVX);
            Array.Reverse(bodyArray_StartingIndexSVY);
            Array.Reverse(bodyArray_StartingIndexSVZ);
            Array.Reverse(bodyArray_NumPixSVX);
            Array.Reverse(bodyArray_NumPixSVY);
            Array.Reverse(bodyArray_NumPixSVZ);
        }

        // Translate the byte arrays into the appropriate data types
        UInt16 versionNumber_bodyIm = BitConverter.ToUInt16(bodyArray_Version);
        UInt16 numPixX_bodyIm = BitConverter.ToUInt16(bodyArray_NumPixX);
        UInt16 numPixY_bodyIm = BitConverter.ToUInt16(bodyArray_NumPixY);
        UInt16 numPixZ_bodyIm = BitConverter.ToUInt16(bodyArray_NumPixZ);
        float xi_bodyIm = BitConverter.ToSingle(bodyArray_Xi);
        float yi_bodyIm = BitConverter.ToSingle(bodyArray_Yi);
        float zi_bodyIm = BitConverter.ToSingle(bodyArray_Zi);
        float xj_bodyIm = BitConverter.ToSingle(bodyArray_Xj);
        float yj_bodyIm = BitConverter.ToSingle(bodyArray_Yj);
        float zj_bodyIm = BitConverter.ToSingle(bodyArray_Zj);
        float xk_bodyIm = BitConverter.ToSingle(bodyArray_Xk);
        float yk_bodyIm = BitConverter.ToSingle(bodyArray_Yk);
        float zk_bodyIm = BitConverter.ToSingle(bodyArray_Zk);
        float centerPosX_bodyIm = BitConverter.ToSingle(bodyArray_CenterPosX);
        float centerPosY_bodyIm = BitConverter.ToSingle(bodyArray_CenterPosY);
        float centerPosZ_bodyIm = BitConverter.ToSingle(bodyArray_CenterPosZ);
        UInt16 startingIndexSVX_bodyIm = BitConverter.ToUInt16(bodyArray_StartingIndexSVX);
        UInt16 startingIndexSVY_bodyIm = BitConverter.ToUInt16(bodyArray_StartingIndexSVY);
        UInt16 startingIndexSVZ_bodyIm = BitConverter.ToUInt16(bodyArray_StartingIndexSVZ);
        UInt16 numPixSVX_bodyIm = BitConverter.ToUInt16(bodyArray_NumPixSVX);
        UInt16 numPixSVY_bodyIm = BitConverter.ToUInt16(bodyArray_NumPixSVY);
        UInt16 numPixSVZ_bodyIm = BitConverter.ToUInt16(bodyArray_NumPixSVZ);

        
        // Store all this values in the ImageInfo structure
        ImageInfo incomingImageInfo = new ImageInfo();
        incomingImageInfo.versionNumber = versionNumber_bodyIm;
        incomingImageInfo.imComp = bodyArray_ImComp[0];
        incomingImageInfo.scalarType = bodyArray_ScalarType[0];
        incomingImageInfo.endian = bodyArray_Endian[0];
        incomingImageInfo.imCoord = bodyArray_ImCoord[0];
        incomingImageInfo.numPixX = numPixX_bodyIm;
        incomingImageInfo.numPixY = numPixY_bodyIm;
        incomingImageInfo.numPixZ = numPixZ_bodyIm;
        incomingImageInfo.xi = xi_bodyIm;
        incomingImageInfo.yi = yi_bodyIm;
        incomingImageInfo.zi = zi_bodyIm;
        incomingImageInfo.xj = xj_bodyIm;
        incomingImageInfo.yj = yj_bodyIm;
        incomingImageInfo.zj = zj_bodyIm;
        incomingImageInfo.xk = xk_bodyIm;
        incomingImageInfo.yk = yk_bodyIm;
        incomingImageInfo.zk = zk_bodyIm;
        incomingImageInfo.centerPosX = centerPosX_bodyIm;
        incomingImageInfo.centerPosY = centerPosY_bodyIm;
        incomingImageInfo.centerPosZ = centerPosZ_bodyIm;
        incomingImageInfo.startingIndexSVX = startingIndexSVX_bodyIm;
        incomingImageInfo.startingIndexSVY = startingIndexSVY_bodyIm;
        incomingImageInfo.startingIndexSVZ = startingIndexSVZ_bodyIm;
        incomingImageInfo.numPixSVX = numPixSVX_bodyIm;
        incomingImageInfo.numPixSVY = numPixSVY_bodyIm;
        incomingImageInfo.numPixSVZ = numPixSVZ_bodyIm;
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
