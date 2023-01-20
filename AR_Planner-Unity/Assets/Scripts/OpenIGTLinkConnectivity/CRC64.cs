// This code is based on: https://github.com/franklinwk/OpenIGTLink-Unity
// Modified by Alicia Pose Díez de la Lastra, from Universidad Carlos III de Madrid

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CRC64
{
    private ulong[] _table;

    private ulong CmTab(int index, ulong poly)
    {
        ulong retval = (ulong)index;
        ulong topbit = (ulong)1L << (64 - 1);
        ulong mask = 0xffffffffffffffffUL;

        retval <<= (64 - 8);
        for (int i = 0; i < 8; i++)
        {
            if ((retval & topbit) != 0)
                retval = (retval << 1) ^ poly;
            else
                retval <<= 1;
        }
        return retval & mask;
    }

    private ulong[] GenStdCrcTable(ulong poly)
    {
        ulong[] table = new ulong[256];
        for (var i = 0; i < 256; i++)
            table[i] = CmTab(i, poly);
        return table;
    }

    private ulong TableValue(ulong[] table, byte b, ulong crc)
    {
        return table[((crc >> 56) ^ b) & 0xffUL] ^ (crc << 8);
    }

    public void Init(ulong poly)
    {
        _table = GenStdCrcTable(poly);
    }

    public ulong Compute(byte[] bytes, ulong initial, ulong final)
    {
        ulong current = initial;
        for (var i = 0; i < bytes.Length; i++)
        {
            current = TableValue(_table, bytes[i], current);
        }
        return current ^ final;

    }
}
