#!/usr/bin/env python3
##################################
# Program is part of SNAP2StaMPS #
# Copyright (c) 2022, Lei Yuan   #
# Author: Lei Yuan, 2022         #
##################################

import os
import subprocess
import sys
import time
import argparse
import glob

COREG_XML = """<graph id="Graph">
  <version>1.0</version>
  <node id="Read">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>MASTER</file>
    </parameters>
  </node>
  <node id="Read(2)">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>SLAVE</file>
    </parameters>
  </node>
  <node id="Back-Geocoding">
    <operator>Back-Geocoding</operator>
    <sources>
      <sourceProduct refid="Read"/>
      <sourceProduct.1 refid="Read(2)"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <demName>SRTM 3Sec</demName>
      <demResamplingMethod>BILINEAR_INTERPOLATION</demResamplingMethod>
      <externalDEMFile/>
      <externalDEMNoDataValue>0.0</externalDEMNoDataValue>
      <resamplingType>BILINEAR_INTERPOLATION</resamplingType>
      <maskOutAreaWithoutElevation>false</maskOutAreaWithoutElevation>
      <outputRangeAzimuthOffset>false</outputRangeAzimuthOffset>
      <outputDerampDemodPhase>false</outputDerampDemodPhase>
      <disableReramp>false</disableReramp>
    </parameters>
  </node>
  <node id="Enhanced-Spectral-Diversity">
    <operator>Enhanced-Spectral-Diversity</operator>
    <sources>
      <sourceProduct refid="Back-Geocoding"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <fineWinWidthStr>512</fineWinWidthStr>
      <fineWinHeightStr>512</fineWinHeightStr>
      <fineWinAccAzimuth>16</fineWinAccAzimuth>
      <fineWinAccRange>16</fineWinAccRange>
      <fineWinOversampling>128</fineWinOversampling>
      <xCorrThreshold>0.1</xCorrThreshold>
      <cohThreshold>0.2</cohThreshold>
      <numBlocksPerOverlap>10</numBlocksPerOverlap>
      <esdEstimator>Periodogram</esdEstimator>
      <weightFunc>Inv Quadratic</weightFunc>
      <temporalBaselineType>Number of images</temporalBaselineType>
      <maxTemporalBaseline>4</maxTemporalBaseline>
      <integrationMethod>L1 and L2</integrationMethod>
      <doNotWriteTargetBands>false</doNotWriteTargetBands>
      <useSuppliedRangeShift>false</useSuppliedRangeShift>
      <overallRangeShift>0.0</overallRangeShift>
      <useSuppliedAzimuthShift>false</useSuppliedAzimuthShift>
      <overallAzimuthShift>0.0</overallAzimuthShift>
    </parameters>
  </node>
  <node id="TOPSAR-Deburst">
    <operator>TOPSAR-Deburst</operator>
    <sources>
      <sourceProduct refid="Enhanced-Spectral-Diversity"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <selectedPolarisations/>
    </parameters>
  </node>
  <node id="Write">
    <operator>Write</operator>
    <sources>
      <sourceProduct refid="TOPSAR-Deburst"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>OUTPUT_COREG_FILE</file>
      <formatName>BEAM-DIMAP</formatName>
    </parameters>
  </node>
  <applicationData id="Presentation">
    <Description/>
    <node id="Back-Geocoding">
      <displayPosition x="190.0" y="146.0"/>
    </node>
    <node id="Enhanced-Spectral-Diversity">
      <displayPosition x="347.0" y="147.0"/>
    </node>
    <node id="TOPSAR-Deburst">
      <displayPosition x="566.0" y="147.0"/>
    </node>
    <node id="Read">
      <displayPosition x="58.0" y="92.0"/>
    </node>
    <node id="Read(2)">
      <displayPosition x="57.0" y="201.0"/>
    </node>
    <node id="Write">
      <displayPosition x="726.0" y="148.0"/>
    </node>
  </applicationData>
</graph>
"""

EXAMPLE = """Example:
  python3 coreg.py /ly/slc /ly/coreg 20201229
"""


def cmdline_parser():
    parser = argparse.ArgumentParser(
        description='Sentinel-1 TOPS coregistration with ESD using SNAP.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('slc_dir', help='slc directory')
    parser.add_argument('output_dir', help='output directory')
    parser.add_argument('master', help='master slc date for coregistration')
    inps = parser.parse_args()

    return inps


if __name__ == "__main__":
    # get inputs
    inps = cmdline_parser()
    slc_dir = os.path.abspath(inps.slc_dir)
    output_dir = os.path.abspath(inps.output_dir)
    master_date = inps.master

    # check inputs
    if not os.path.isdir(slc_dir):
        sys.exit(f"Error, {slc_dir} does not exist.")

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    xml_dir = os.path.join(output_dir, 'xml')
    if not os.path.isdir(xml_dir):
      os.mkdir(xml_dir)

    dims = glob.glob(os.path.join(slc_dir, "*.dim"))
    if len(dims) < 2:
        sys.exit(f"No enough slc file in {slc_dir}")

    slaves = [i for i in dims if master_date not in os.path.basename(i)]

    for slave in slaves:
        index = slaves.index(slave) + 1
        slave_name = os.path.basename(slave)
        print(f"\n[{index}/{len(slaves)}] Processing file: {slave_name}\n")

        master = os.path.join(slc_dir, master_date + slave_name[8:])

        xml_data = COREG_XML
        xml_data = xml_data.replace('MASTER', master)
        xml_data = xml_data.replace('SLAVE', slave)
        output_file = os.path.join(output_dir, f"{master_date}_{slave_name}")
        xml_data = xml_data.replace('OUTPUT_COREG_FILE', output_file)

        xml_name = f"{master_date}_{slave_name[0:-4]}_coreg.xml"
        xml_path = os.path.join(xml_dir, xml_name)
        with open(xml_path, 'w+') as f:
            f.write(xml_data)

        args = ['gpt', xml_path]
        process = subprocess.Popen(args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        time_start = time.time()

        stdout = process.communicate()[0]
        print(str(stdout, encoding='utf-8'))

        time_delta = time.time() - time_start
        print('Finished in {} seconds.'.format(time_delta))

        if process.returncode != 0:
            print('Error coregistration with file {}\n'.format(slave_name))
        else:
            print('Complete coregistration with file {}\n'.format(slave_name))
