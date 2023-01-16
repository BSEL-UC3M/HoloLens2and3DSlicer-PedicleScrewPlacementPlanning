// Code retrieved from: https://github.com/BIIG-UC3M/IGT-UltrARsound
/*
* Code created by Marius Krusen
* Modified by Niklas Kompe, Johann Engster, Phillip Overloeper
*/

using System;
using System.Text;
using UnityEngine;
using System.Collections.Generic;

#if UNITY_EDITOR
using System.Net.Sockets;
#else
using System.Threading.Tasks;
using System.IO;
using Windows.Networking.Sockets;
using Windows.Storage.Streams;
using Windows.Networking;
using Windows.Foundation;
#endif


/// <summary>
/// The class to communicate with the server socket.
/// </summary>
public class SocketHandler
{
    // Objects for the tcp communication (for Unity Editor)
#if UNITY_EDITOR
    // Implementation with TcpClient
    /// <summary>
    /// Tcp client for server communication (unity editor)
    /// </summary>
    private TcpClient tcpClient;

    /// <summary>
    /// Stream to receive and send massages (unity editor)
    /// </summary>
    private NetworkStream clientStream;
#else
    // Implementation with Socket (for HoloLens)
    /// <summary>
    /// Socket for server communication.
    /// </summary>
    private StreamSocket socket;

    /// <summary>
    /// Data Writer to write massages.
    /// </summary>
    private DataWriter dw;

    /// <summary>
    /// Data Reader to receive massages.
    /// </summary>
    private DataReader dr;
#endif


    /// <summary>
    /// Constructor to create a socket to communicate.
    /// </summary>
    public SocketHandler()
    {
#if !UNITY_EDITOR
        socket = new StreamSocket();
#endif
    }

#if UNITY_EDITOR
    /// <summary>
    /// Connects socket to server.
    /// </summary>
    /// <param name="ip">Server ip</param>
    /// <param name="port">Server port</param>
    /// <returns>If socket connection was successfull.</returns>
    public bool Connect(string ip, int port)
    {
        try
        {
            // Create a TcpClient
            tcpClient = new TcpClient(ip, port);
            // Create clientStream further communication
            clientStream = tcpClient.GetStream();
            return true;
        }
        catch (Exception e)
        {
            Debug.Log("Connecting exception editor " + e);
        }
        return false;
    }
#else
    /// <summary>
    /// Connects socket to server.
    /// </summary>
    /// <param name="ip">Server ip</param>
    /// <param name="port">Server port</param>
    /// <returns>If socket connection was successfull.</returns>
    public bool Connect(string ip, int port)
    {
        try
        {
            // Connect socket
            HostName host = new HostName(ip);
            IAsyncAction action = socket.ConnectAsync(host, port.ToString());
            IAsyncAction timeout = Task.Delay(5000).AsAsyncAction();

            // Block the thread while connecting or timeout
            while (action.Status != AsyncStatus.Completed)
            {
                // Check if the timeout is reached
                if (timeout.Status == AsyncStatus.Completed)
                {
                    Debug.Log("Connection timeout");
                    action.Cancel();
                    return false;
                }
            }

            // Create DataWriter and DataReader for further communication
            dw = new DataWriter(socket.OutputStream);
            dr = new DataReader(socket.InputStream);
            dr.InputStreamOptions = InputStreamOptions.Partial;
            return true;
        }
        catch (Exception e)
        {
            Debug.Log("Connecting exception: " + e);
        }
        return false;
    }
#endif

#if UNITY_EDITOR
    /// <summary>
    /// Method to send strings to the server.
    /// </summary>
    /// <param name="msg">Massage to be send.</param>
    public void Send(String msg)
    {
        byte[] msgAsByteArray = Encoding.ASCII.GetBytes(msg);
        Send(msgAsByteArray);
    }
#else
    /// <summary>
    /// Method to send strings to the server.
    /// </summary>
    /// <param name="msg">Massage to be send.</param>
    public async void Send(String msg)
    {
        dw.WriteString(msg);
        await dw.StoreAsync();
        await dw.FlushAsync();
    }
#endif

#if UNITY_EDITOR
    /// <summary>
    /// Method to send bytes to the server.
    /// </summary>
    /// <param name="msg">Massage to be send.</param>
    public void Send(byte[] msg)
    {
        if (clientStream.CanWrite)
        {
            clientStream.Write(msg, 0, msg.Length);
        }
    }
#else
    /// <summary>
    /// Method to send bytes to the server.
    /// </summary>
    /// <param name="msg">Massage to be send.</param>
    public async void Send(byte[] msg)
    {
        dw.WriteBytes(msg);
        await dw.StoreAsync();
        await dw.FlushAsync();
    }
#endif


    /// <summary>
    /// Method to receive a byte array from the server.
    /// </summary>
    /// <returns>Massage the server has sent.</returns>
    public byte[] Listen(uint msgSize)
    {
#if UNITY_EDITOR
        
        
        Byte[] bytes = new Byte[msgSize]; ////////////////////////////////////////////////////////////////// Size of transform message ///////////////////////////
        List<byte> byteList = new List<byte>();
        StringBuilder receivedMsg = new StringBuilder();
        int readBytes = 0;

        while (clientStream.CanRead && clientStream.DataAvailable)
        {
            readBytes = clientStream.Read(bytes, 0, bytes.Length);
            receivedMsg.AppendFormat("{0}", Encoding.ASCII.GetString(bytes, 0, readBytes));
            byteList.AddRange(bytes);
        }

        byte[] allBytes = new byte[byteList.Count];
        allBytes = byteList.ToArray();
        return allBytes;
#else

       
        byte[] allBytes;
        var loadaction = dr.LoadAsync(msgSize); /////////////////////////////////////////////////////////// Size of transform message ///////////////////////////
        // Block the thread while loading
        while (loadaction.Status != AsyncStatus.Completed)
        {
        }

        if (loadaction.GetResults() > 0)
        {
            allBytes = new byte[loadaction.GetResults()];
            dr.ReadBytes(allBytes);
        }
        else
        {
            allBytes = new byte[0];
        }

        return allBytes;
#endif
    }

    public void Disconnect()
    {
#if UNITY_EDITOR
        if (tcpClient != null)
        {
            clientStream.Close();
            tcpClient.Close();
            tcpClient = null;
        }
#else
        if (socket != null)
        {
            socket.Dispose();
            socket = null;
        }
#endif
    }
}
