#!/usr/bin/env python3
##################################
# Program is part of SNAP2StaMPS #
# Copyright (c) 2022, Lei Yuan   #
# Author: Lei Yuan, 2022         #
##################################

import argparse
import glob
import os
import subprocess
import sys
import time

IFG_XML = """<graph id="Graph">
  <version>1.0</version>
  <node id="Read">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>COREG_FILE</file>
    </parameters>
  </node>
  <node id="Interferogram">
    <operator>Interferogram</operator>
    <sources>
      <sourceProduct refid="Read"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <subtractFlatEarthPhase>true</subtractFlatEarthPhase>
      <srpPolynomialDegree>5</srpPolynomialDegree>
      <srpNumberPoints>501</srpNumberPoints>
      <orbitDegree>3</orbitDegree>
      <includeCoherence>true</includeCoherence>
      <cohWinAz>2</cohWinAz>
      <cohWinRg>10</cohWinRg>
      <squarePixel>true</squarePixel>
      <subtractTopographicPhase>true</subtractTopographicPhase>
      <demName>SRTM 3Sec</demName>
      <externalDEMFile/>
      <externalDEMNoDataValue>0.0</externalDEMNoDataValue>
      <externalDEMApplyEGM>true</externalDEMApplyEGM>
      <tileExtensionPercent>100</tileExtensionPercent>
      <outputElevation>true</outputElevation>
      <outputLatLon>true</outputLatLon>
    </parameters>
  </node>
  <node id="Write">
    <operator>Write</operator>
    <sources>
      <sourceProduct refid="Interferogram"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>OUTPUT_IFG_FILE</file>
      <formatName>BEAM-DIMAP</formatName>
    </parameters>
  </node>
  <applicationData id="Presentation">
    <Description/>
    <node id="Read">
      <displayPosition x="38.0" y="89.0"/>
    </node>
    <node id="Interferogram">
      <displayPosition x="208.0" y="91.0"/>
    </node>
    <node id="Write">
      <displayPosition x="396.0" y="91.0"/>
    </node>
  </applicationData>
</graph>
"""

EXAMPLE = """Example:
  python3 ifg.py /ly/coreg /ly/ifg
"""


def cmdline_parser():
    parser = argparse.ArgumentParser(
        description='Product interferogram using SNAP.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('input_dir', help='input directory')
    parser.add_argument('output_dir', help='output directory')
    inps = parser.parse_args()

    return inps


if __name__ == "__main__":
    # get inputs
    inps = cmdline_parser()
    input_dir = os.path.abspath(inps.input_dir)
    output_dir = os.path.abspath(inps.output_dir)

    # check inputs
    if not os.path.isdir(input_dir):
        sys.exit(f"Error, {input_dir} does not exist.")

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    xml_dir = os.path.join(output_dir, 'xml')
    if not os.path.isdir(xml_dir):
      os.mkdir(xml_dir)

    dims = glob.glob(os.path.join(input_dir, "*.dim"))
    if len(dims) == 0:
        sys.exit(f"Cannot find any dim file in {input_dir}")

    for dim in dims:
        index = dims.index(dim) + 1
        dim_name = os.path.basename(dim)
        print(f"\n[{index}/{len(dims)}] Processing file: {dim_name}\n")

        xml_data = IFG_XML
        xml_data = xml_data.replace('COREG_FILE', dim)
        output_file = os.path.join(output_dir, dim_name)
        xml_data = xml_data.replace('OUTPUT_IFG_FILE', output_file)

        xml_name = dim_name[0:-4] + '_ifg.xml'
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
            print('Error producting interferogram with file {}\n'.format(dim_name))
        else:
            print('Complete producting interferogram with file {}\n'.format(dim_name))
