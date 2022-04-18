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

MERGE_2IW_XML = """<graph id="Graph">
  <version>1.0</version>
  <node id="Read">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>IW1_FILE</file>
    </parameters>
  </node>
  <node id="Read(2)">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>IW2_FILE</file>
    </parameters>
  </node>
  <node id="TOPSAR-Merge">
    <operator>TOPSAR-Merge</operator>
    <sources>
      <sourceProduct refid="Read"/>
      <sourceProduct.1 refid="Read(2)"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <selectedPolarisations/>
    </parameters>
  </node>
  <node id="Write">
    <operator>Write</operator>
    <sources>
      <sourceProduct refid="TOPSAR-Merge"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>OUTPUT_MERGED_FILE</file>
      <formatName>BEAM-DIMAP</formatName>
    </parameters>
  </node>
  <applicationData id="Presentation">
    <Description/>
    <node id="Read">
      <displayPosition x="40.0" y="95.0"/>
    </node>
    <node id="Read(2)">
      <displayPosition x="41.0" y="190.0"/>
    </node>
    <node id="TOPSAR-Merge">
      <displayPosition x="173.0" y="144.0"/>
    </node>
    <node id="Write">
      <displayPosition x="378.0" y="145.0"/>
    </node>
  </applicationData>
</graph>
"""

MERGE_3IW_XML = """<graph id="Graph">
  <version>1.0</version>
  <node id="Read">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>IW1_FILE</file>
    </parameters>
  </node>
  <node id="Read(2)">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>IW2_FILE</file>
    </parameters>
  </node>
  <node id="Read(3)">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>IW3_FILE</file>
    </parameters>
  </node>
  <node id="TOPSAR-Merge">
    <operator>TOPSAR-Merge</operator>
    <sources>
      <sourceProduct refid="Read"/>
      <sourceProduct.1 refid="Read(2)"/>
      <sourceProduct.2 refid="Read(3)"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <selectedPolarisations/>
    </parameters>
  </node>
  <node id="Write">
    <operator>Write</operator>
    <sources>
      <sourceProduct refid="TOPSAR-Merge"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>OUTPUT_MERGED_FILE</file>
      <formatName>BEAM-DIMAP</formatName>
    </parameters>
  </node>
  <applicationData id="Presentation">
    <Description/>
    <node id="Read">
      <displayPosition x="39.0" y="37.0"/>
    </node>
    <node id="Read(2)">
      <displayPosition x="42.0" y="104.0"/>
    </node>
    <node id="Read(3)">
      <displayPosition x="42.0" y="172.0"/>
    </node>
    <node id="TOPSAR-Merge">
      <displayPosition x="203.0" y="106.0"/>
    </node>
    <node id="Write">
      <displayPosition x="390.0" y="105.0"/>
    </node>
  </applicationData>
</graph>
"""

EXAMPLE = """Example:
  python3 merge.py /ly/coreg /ly/coreg_merge
"""


def cmdline_parser():
    parser = argparse.ArgumentParser(
        description='Sentinel-1 TOPS merge using SNAP.',
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

    # get IW
    iw = [i[-5:-4] for i in dims]
    iw = sorted(list(set(iw)))

    # get master_slave
    pairs = [os.path.basename(i)[0:17] for i in dims]
    pairs = sorted(list(set(pairs)))

    for pair in pairs:
        if len(iw) == 1:
            print("No need to merge.")

        if len(iw) == 2:
            iw1_file = os.path.join(input_dir, f"{pair}_IW{iw[0]}.dim")
            iw2_file = os.path.join(input_dir, f"{pair}_IW{iw[1]}.dim")
            output_file = os.path.join(output_dir, f"{pair}_IW{''.join(iw)}.dim")

            xml_data = MERGE_2IW_XML
            xml_data = xml_data.replace('IW1_FILE', iw1_file)
            xml_data = xml_data.replace('IW2_FILE', iw2_file)
            xml_data = xml_data.replace('OUTPUT_MERGED_FILE', output_file)

        if len(iw) == 3:
            iw1_file = os.path.join(input_dir, f"{pair}_IW{iw[0]}.dim")
            iw2_file = os.path.join(input_dir, f"{pair}_IW{iw[1]}.dim")
            iw3_file = os.path.join(input_dir, f"{pair}_IW{iw[2]}.dim")
            output_file = os.path.join(output_dir, f"{pair}_IW{''.join(iw)}.dim")

            xml_data = MERGE_3IW_XML
            xml_data = xml_data.replace('IW1_FILE', iw1_file)
            xml_data = xml_data.replace('IW2_FILE', iw2_file)
            xml_data = xml_data.replace('IW3_FILE', iw3_file)
            xml_data = xml_data.replace('OUTPUT_MERGED_FILE', output_file)

        index = pairs.index(pair) + 1
        print(f"\n[{index}/{len(pairs)}] Processing pair: {pair}\n")

        xml_name = pair + '_merge.xml'
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
            print('Error merging pair {}\n'.format(pair))
        else:
            print('Complete merging pair {}\n'.format(pair))
