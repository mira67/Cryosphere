#!/usr/bin/env python

copyright_notice= """
    jpeg_read.py - jpeg decoder.
    Copyright (C) 2010 Mats Alritzson 

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
    Modified from: https://github.com/enmasse/jpeg_read
"""
import sys
from math import *
#from Tkinter import *
#from memoize import *

class JpegDecoder():
    def __init__(self):
        self.huffman_ac_tables= [{}, {}, {}, {}]
        self.huffman_dc_tables= [{}, {}, {}, {}]
        
        self.q_table= [[], [], [], []]
        
        self.XYP= 0, 0, 0
        self.component= {}
        self.num_components= 0
        self.mcus_read= 0
        self.dc= []
        self.inline_dc= 0
        
        self.idct_precision= 8
        
        self.EOI= False
        self.data= []
        self.bit_stream = None
        # Lookup table to speed up IDCT somewhat
        self.idct_table= [ [(self.C(u)*cos(((2.0*x+1.0)*u*pi)/16.0)) for x in range(self.idct_precision)] for u in range(self.idct_precision) ]

        
    def read_word(self,file):
        """ Read a 16 bit word from file """
        out= ord(file.read(1)) << 8
        out|= ord(file.read(1))
        return out
        
    def read_byte(self,file):
        """ Read a byte from file """
        out= ord(file.read(1))
        return out
        
        
    def read_dht(self,file):
        """ Read and compute the huffman tables """        
        # Read the marker length
        Lh= self.read_word(file)
        Lh-= 2
        while Lh>0:
            huffsize= []
            huffval= []
            T= self.read_byte(file)
            Th= T & 0x0F
            Tc= (T >> 4) & 0x0F
            Lh= Lh-1
        
            # Read how many symbols of each length
            # up to 16 bits
            for i in range(16):
                huffsize.append(self.read_byte(file))
                Lh-= 1
        
            # Generate the huffman codes
            huffcode= self.huffman_codes(huffsize)        
            # Read the values that should be mapped to
            # huffman codes
            for i in huffcode:
                huffval.append(self.read_byte(file))
                Lh-= 1
        
            # Generate lookup tables
            if Tc==0:
                self.huffman_dc_tables[Th]= self.map_codes_to_values(huffcode, huffval)
            else:
                self.huffman_ac_tables[Th]= self.map_codes_to_values(huffcode, huffval)
        
    def map_codes_to_values(self,codes, values):
        """ Map the huffman code to the right value """
        out= {}
    
        for i in range(len(codes)):
            out[codes[i]]= values[i]
    
        return out
    
    def huffman_codes(self,huffsize):
        """ Calculate the huffman code of each length """
        huffcode= []
        k= 0
        code= 0
    
    # Magic
        for i in range(len(huffsize)):
            si= huffsize[i]
            for k in range(si):
                huffcode.append((i+1,code))
                code+= 1
    
            code<<= 1
    
        return huffcode
    
    def read_dqt(self,file):
        """ Read the quantization table. 
        The table is in self.zigzag order """
    
        Lq= self.read_word(file)
        Lq-= 2
        while Lq>0:
            table= []
            Tq= self.read_byte(file)
            Pq= Tq >> 4
            Tq&= 0xF
            Lq-= 1
    
            if Pq==0:
                for i in range(64):
                    table.append(self.read_byte(file))
                    Lq-= 1
    
            else:
                for i in range(64):
                    val= self.read_word(file)
                    table.append(val)
                    Lq-= 2   
    
            self.q_table[Tq]= table
    
    
    def read_sof(self,type, file):
        """ Read the start of frame marker """        
        # Read the marker length
        Lf= self.read_word(file)
        Lf-= 2
        # Read the sample precision
        P= self.read_byte(file)
        Lf-= 1
        # Read number of lines
        Y= self.read_word(file)
        Lf-= 2
        # Read the number of sample per line
        X= self.read_word(file)
        Lf-= 2
        # Read number of self.components
        Nf= self.read_byte(file)
        Lf-= 1
        
        self.XYP= X, Y, P
        
        while Lf>0:
        # Read self.component identifier
            C= self.read_byte(file)
            # Read sampling factors
            V= self.read_byte(file)
            Tq= self.read_byte(file)
            Lf-= 3
            H= V >> 4
            V&= 0xF
            self.component[C]= {}
            # Assign horizontal sampling factor
            self.component[C]['H']= H
            # Assign vertical sampling factor
            self.component[C]['V']= V
            # Assign quantization table
            self.component[C]['Tq']= Tq
            
    
    def read_app(self,type, file):
        """ Read APP marker """
        Lp= self.read_word(file)
        Lp-= 2
        
        # If APP0 try to read the JFIF header
        # Not really necessary
        if type==0:
            identifier= file.read(5)
            Lp-= 5
            version= file.read(2)
            Lp-= 2
            units= ord(file.read(1))
            Lp-= 1
            Xdensity= ord(file.read(1)) << 8
            Xdensity|= ord(file.read(1))
            Lp-= 2
            Ydensity= ord(file.read(1)) << 8
            Ydensity|= ord(file.read(1))
            Lp-= 2
            
        file.seek(Lp, 1)
        
    
    def read_dnl(self,file):
        """Read the DNL marker Changes the number of lines """ 
        Ld= self.read_word(file)
        Ld-= 2
        NL= self.read_word(file)
        Ld-= 2
        
        X, Y, P= self.XYP
        
        if Y==0:
            self.XYP= X, NL, P
        
    def read_sos(self,file):
        """ Read the start of scan marker """ 
        Ls= self.read_word(file)
        Ls-= 2
        
        # Read number of self.components in scan
        Ns= self.read_byte(file)
        Ls-= 1
        
        for i in range(Ns):
            # Read the scan self.component selector
            Cs= self.read_byte(file)
            Ls-= 1
            # Read the huffman table selectors
            Ta= self.read_byte(file)
            Ls-= 1
            Td= Ta >> 4
            Ta&= 0xF
            # Assign the DC huffman table
            self.component[Cs]['Td']= Td
            # Assign the AC huffman table
            self.component[Cs]['Ta']= Ta
            
        # Should be zero if baseline DCT
        Ss= self.read_byte(file)
        Ls-= 1
        # Should be 63 if baseline DCT
        Se= self.read_byte(file)
        Ls-= 1
        # Should be zero if baseline DCT
        A= self.read_byte(file)
        Ls-= 1
        
        self.num_components= Ns
        self.dc= [0 for i in range(self.num_components+1)]
        
    
   # @memoize
    def calc_add_bits(self,len, val):
        """ Calculate the value from the "additional" bits in the huffman self.data. """
        if (val & (1 << len-1)):
            pass
        else:
            val-= (1 << len) -1
    
        return val
    
    def bit_read(self,file):
        """ Read one bit from file and handle markers and byte stuffing This is a generator function, google it. """
    
        input= file.read(1)
        while input and not self.EOI:
            if input==chr(0xFF):
                cmd= file.read(1)
                if cmd:
                # Byte stuffing
                    if cmd==chr(0x00):
                        input= chr(0xFF)
                        # End of image marker
                    elif cmd==chr(0xD9):
                        self.EOI= True
                        # Restart markers
                    elif 0xD0 <= ord(cmd) <= 0xD7 and self.inline_dc:
                        # Reset dc value
                        self.dc= [0 for i in range(self.num_components+1)]
                        input= file.read(1)
                    else:
                        input= file.read(1)        
            if not self.EOI:
                for i in range(7, -1, -1):
                    # Output next bit
                    yield (ord(input) >> i) & 0x01
    
                input= file.read(1)
    
        while True:
            yield []
    
    
    def get_bits(self,num, gen):
        """ Get "num" bits from gen """
        out= 0
        for i in range(num):
            out<<= 1
            val= gen.next()
            if val!= []:
                out+= val & 0x01
            else:
                return []
    
        return out
    
    
    def print_and_pause(self,fn):
        def new(*args):
            x= fn(*args)
            print x
            raw_input()
            return x
        return new
    
    #@self.print_and_pause
    def read_data_unit(self,comp_num):
        """ Read one DU with self.component id comp_num """ 
        datal= []
        
        comp= self.component[comp_num]   
        huff_tbl= self.huffman_dc_tables[comp['Td']]
        
        # Fill self.data with 64 coefficients
        while len(datal)< 64:
            key= 0
        
            for bits in range(1, 17):
                key_len= []
                key<<= 1
                # Get one bit from bit_stream
                val= self.get_bits(1, self.bit_stream)
                if val==[]:
                    break
                key|= val
                # If huffman code exists
                if huff_tbl.has_key((bits,key)):
                    key_len= huff_tbl[(bits,key)]
                    break
        
            # After getting the DC value
            # switch to the AC table
            huff_tbl= self.huffman_ac_tables[comp['Ta']]
        
            if key_len==[]:
                print (bits, key, bin(key)), "key not found"
                break
            # If ZRL fill with 16 zero coefficients
            elif key_len==0xF0:
                for i in range(16):
                    datal.append(0)
                continue
        
            # If not DC coefficient
            if len(datal)!=0:
                # If End of block
                if key_len==0x00:
                # Fill the rest of the DU with zeros
                    while len(datal)< 64:
                        datal.append(0)
                    break
        
                # The first part of the AC key_len
                # is the number of leading zeros
                for i in range(key_len >> 4):
                    if len(datal)<64:
                        datal.append(0)
                key_len&= 0x0F
        
        
            if len(datal)>=64:
                break
        
            if key_len!=0:
                # The rest of key_len is the amount
                # of "additional" bits
                val= self.get_bits(key_len, self.bit_stream)
                if val==[]:
                    break
                # Decode the additional bits
                num= self.calc_add_bits(key_len, val)
        
                # Experimental, doesn't work right
                if len(datal)==0 and self.inline_dc:
                    # The DC coefficient value
                    # is added to the DC value from
                    # the corresponding DU in the
                    # previous MCU
                    num+= self.dc[comp_num]
                    self.dc[comp_num]= num
        
                datal.append(num)
            else:
                datal.append(0)
        
        if len(datal)!=64:
            print "Wrong size", len(datal)
        
        return datal

    def restore_dc(self):
        out= []
        dctest = []
        try:
            dc_prev= [0 for x in range(len(self.data[0]))]
                  # For each MCU
            for mcu in self.data:
              #print "mcu"
              #print len(self.data)
              #print mcu
              # For each self.component
                for comp_num in range(len(mcu)):
                 # For each DU
                    for du in range(len(mcu[comp_num])):
                        if mcu[comp_num][du]:
                            mcu[comp_num][du][0]+= dc_prev[comp_num]
                            dctest.append(mcu[comp_num][du][0])
                            dc_prev[comp_num]= mcu[comp_num][du][0]

                out.append(mcu)
        except IndexError, e:
            dctest = [6,7,7]

        return dctest
        #return out


    def read_mcu(self):
       """ Read an MCU """

       comp_num= mcu= range(self.num_components)
             
       # For each self.component
       for i in comp_num:
          comp= self.component[i+1]
          mcu[i]= []
          # For each DU
          for j in range(comp['H']*comp['V']):     
             if not self.EOI:
                mcu[i].append(self.read_data_unit(i+1))

       self.mcus_read+= 1

       return mcu


    def dequantify(self,mcu):
       """ Dequantify MCU """
       out= mcu

       # For each self.component
       for c in range(len(out)):
          # For each DU
          for du in range(len(out[c])):
             # For each coefficient
             for i in range(len(out[c][du])):
                # Multiply by the the corresponding
                # value in the quantization table
                out[c][du][i]*= self.q_table[self.component[c+1]['Tq']][i]

       return out

    def zagzig(self,du):
       """ Put the coefficients in the right order """
       map= [[ 0,  1,  5,  6, 14, 15, 27, 28],
             [ 2,  4,  7, 13, 16, 26, 29, 42],
             [ 3,  8, 12, 17, 25, 30, 41, 43],
             [ 9, 11, 18, 24, 31, 40, 44, 53],
             [10, 19, 23, 32, 39, 45, 52, 54],
             [20, 22, 33, 38, 46, 51, 55, 60],
             [21, 34, 37, 47, 50, 56, 59, 61],
             [35, 36, 48, 49, 57, 58, 62, 63]]

       # Iterate over 8x8
       for x in range(8):
          for y in range(8):
             if map[x][y]<len(du):
                map[x][y]= du[map[x][y]]
             else:
                # If DU is too short
                # This shouldn't happen.
                map[x][y]= 0

       return map

    def for_each_du_in_mcu(self,mcu, func):
       """ Helper function that iterates over all DU's in an MCU and runs "func" on it """
       return [ map(func, comp) for comp in mcu ]

#@memoize
    def C(self,x):
       if x==0:
          return 1.0/sqrt(2.0)
       else:
          return 1.0

    def idct(self,matrix):
       """ Converts from frequency domain ordinary(?) """
       range8= range(8)
       rangeIDCT= range(self.idct_precision)
       out= [ range(8) for i in range(8)]

       # Iterate over every pixel in the block
       for x in range8:
          for y in range8:
             sum= 0

             # Iterate over every coefficient
             # in the DU
             for u in rangeIDCT:
                for v in rangeIDCT:
                   sum+= matrix[v][u]*self.idct_table[u][x]*self.idct_table[v][y]

             out[y][x]= sum//4

       return out

    def expand(self,mcu, H, V):
       """ Reverse subsampling """
       Hout= max(H)
       Vout= max(V)
       out= [ [ [] for x in range(8*Hout) ] for y in range(8*Vout) ]

       for i in range(len(mcu)):
          Hs= Hout//H[i]
          Vs= Vout//V[i]
          Hin= H[i]
          Vin= V[i]
          comp= mcu[i]

          if len(comp)!=(Hin*Vin):
             return []

          for v in range(Vout):
             for h in range(Hout):
                for y in range(8):
                   for x in range(8):
                      out[y+v*8][x+h*8].append(comp[(h//Hs)+Hin*(v//Vs)][y//Vs][x//Hs])

       return out


    def combine_mcu(self,mcu):
       H= []
       V= []

       for i in range(self.num_components):
          H.append(self.component[i+1]['H'])
          V.append(self.component[i+1]['V'])

       return self.expand(mcu, H, V)


    def combine_blocks(self):
       X, Y, P= self.XYP   

       out= [ [ (0, 0, 0) for x in range(X+32) ] for y in range(Y+64) ]
       offsetx= 0
       offsety= 0

       for block in self.data:
          ybmax= len(block)
          for yb in range(ybmax):
             xbmax= len(block[yb])
             for xb in range(xbmax):
                out[yb+offsety][xb+offsetx]= tuple(block[yb][xb])
          offsetx+= xbmax
          if offsetx>X:
             offsetx= 0
             offsety+= ybmax

       return out


    def crop_image(self):
       X, Y, P= self.XYP
       return [ [ self.data[y][x] for x in range(X) ] for y in range(Y) ]


    def clip(self,x):
       if x>255:
          return 255
       elif x<0:
          return 0
       else:
          return int(x)

    def clamp(self,x):
        x = (abs(x) + x ) // 2
        if x > 255:
            return 255
        else:
            return x

   # @memoize
    def YCbCr2RGB(self,Y, Cb, Cr):
       Cred= 0.299
       Cgreen= 0.587
       Cblue= 0.114

       R= Cr*(2-2*Cred)+Y
       B= Cb*(2-2*Cblue)+Y
       G= (Y-Cblue*B-Cred*R)/Cgreen

       return clamp(R+128), clamp(G+128), clamp(B+128)


    def YCbCr2Y(self,Y, Cb, Cr):
       return Y, Y, Y


    def for_each_pixel(self, func):
       out= [ [0 for pixel in range(len(self.data[0]))] for line in range(len(self.data))]

       for line in range(len(self.data)):
          for pixel in range(len(self.data[0])):
             out[line][pixel]= func(*self.data[line][pixel])

       return out


    def tuplify(self):
       out= []

       for line in self.data:
          out.append(tuple(line))

       return tuple(out)

   # @memoize
   # def prepare(x, y, z):
   #    return "#%02x%02x%02x" % (x, y, z)


    def display_image(self):
       X, Y, P= self.XYP

       #root= Tk()
       #im= PhotoImage(width=X, height=Y)

       #im.put(self.data)

       #w= Label(root, image=im, bd=0)
       #w.pack()

       #mainloop()

    def jpdecode(self,input_file):
        in_char = input_file.read(1)
        while in_char:
            if in_char==chr(0xff):
                in_char= input_file.read(1)
                in_num= ord(in_char)
                if in_num==0xd8:
                   # print "SOI",
                   pass
                elif 0xe0<=in_num<=0xef:
                   # print "APP%x" % (in_num-0xe0),
                    self.read_app(in_num-0xe0, input_file)
                elif 0xd0<=in_num<=0xd7:
                    #print "RST%x" % (in_num-0xd0),
                    pass
                elif in_num==0xdb:
                    #print "DQT",
                    self.read_dqt(input_file)
                elif in_num==0xdc:
                    #print "DNL",
                    self.read_dnl(input_file)
                elif in_num==0xc4:
                    #print "DHT",
                    self.read_dht(input_file)
                elif in_num==0xc8:
                    #print "JPG",
                    pass
                elif in_num==0xcc:
                    #print "DAC"
                    pass
                elif 0xc0<=in_num<=0xcf:
                    #print "SOF%x" % (in_num-0xc0),
                    self.read_sof(in_num-0xc0, input_file)
                elif in_num==0xda:
                    #print "SOS",
                    self.read_sos(input_file)
                    self.bit_stream= self.bit_read(input_file)
                    while not self.EOI:
                        #print "not decoder.EOI"
                        self.data.append(self.read_mcu())
                        #print len(self.data)
                elif in_num==0xd9:
                    #print "EOI",
                    pass

                #print "FF%02X" % in_num
            in_char= input_file.read(1)
        dclist = []
        #print "dcoder.data"
        #print len(self.data)
        if not self.inline_dc:
         #   print "restore dc"
            dclist = self.restore_dc()
         #   print len(dclist)
        return dclist

#in_file = open('1.jpg','rb')
#jd = JpegDecoder()
#dclist = jd.jpdecode(in_file)
#print dclist
#in_file.close()

