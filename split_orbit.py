#!/usr/bin/env python3
##################################
# Program is part of SNAP2StaMPS #
# Copyright (c) 2022, Lei Yuan   #
# Author: Lei Yuan, 2022         #
##################################

import argparse
import glob
import os
import re
import subprocess
import sys
import time

SPLIT_ORBIT_XML = """<graph id="Graph">
  <version>1.0</version>
  <node id="Read">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>INPUTFILE</file>
    </parameters>
  </node>
  <node id="TOPSAR-Split">
    <operator>TOPSAR-Split</operator>
    <sources>
      <sourceProduct refid="Read"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <subswath>IW</subswath>
      <selectedPolarisations>VV</selectedPolarisations>
      <firstBurstIndex>FIRSTBURST</firstBurstIndex>
      <lastBurstIndex>LASTBURST</lastBurstIndex>
      <wktAoi/>
    </parameters>
  </node>
  <node id="Apply-Orbit-File">
    <operator>Apply-Orbit-File</operator>
    <sources>
      <sourceProduct refid="TOPSAR-Split"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <orbitType>Sentinel Precise (Auto Download)</orbitType>
      <polyDegree>3</polyDegree>
      <continueOnFail>false</continueOnFail>
    </parameters>
  </node>
  <node id="Write">
    <operator>Write</operator>
    <sources>
      <sourceProduct refid="Apply-Orbit-File"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>OUTPUTFILE</file>
      <formatName>BEAM-DIMAP</formatName>
    </parameters>
  </node>
  <applicationData id="Presentation">
    <Description/>
    <node id="Read">
            <displayPosition x="37.0" y="134.0"/>
    </node>
    <node id="TOPSAR-Split">
      <displayPosition x="162.0" y="131.0"/>
    </node>
    <node id="Apply-Orbit-File">
      <displayPosition x="320.0" y="131.0"/>
    </node>
    <node id="Write">
            <displayPosition x="455.0" y="133.0"/>
    </node>
  </applicationData>
</graph>
"""
ASSEMBLY_SPLIT_ORBIT_XML = """<graph id="Graph">
  <version>1.0</version>
  <node id="ProductSet-Reader">
    <operator>ProductSet-Reader</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <fileList>FILELIST</fileList>
    </parameters>
  </node>
  <node id="SliceAssembly">
    <operator>SliceAssembly</operator>
    <sources>
      <sourceProduct.2 refid="ProductSet-Reader"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <selectedPolarisations>VV</selectedPolarisations>
    </parameters>
  </node>
  <node id="TOPSAR-Split">
    <operator>TOPSAR-Split</operator>
    <sources>
      <sourceProduct refid="SliceAssembly"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <subswath>IW</subswath>
      <selectedPolarisations/>
      <firstBurstIndex>FIRSTBURST</firstBurstIndex>
      <lastBurstIndex>LASTBURST</lastBurstIndex>
      <wktAoi/>
    </parameters>
  </node>
  <node id="Write">
    <operator>Write</operator>
    <sources>
      <sourceProduct refid="TOPSAR-Split"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>OUTPUTFILE</file>
      <formatName>BEAM-DIMAP</formatName>
    </parameters>
  </node>
  <applicationData id="Presentation">
    <Description/>
    <node id="SliceAssembly">
      <displayPosition x="165.0" y="61.0"/>
    </node>
    <node id="TOPSAR-Split">
      <displayPosition x="300.0" y="61.0"/>
    </node>
    <node id="Write">
      <displayPosition x="415.0" y="61.0"/>
    </node>
    <node id="ProductSet-Reader">
      <displayPosition x="15.0" y="61.0"/>
    </node>
  </applicationData>
</graph>
"""

EXAMPLE = """Example:
  python3 split_orbit.py /ly/zips /ly/slc date.info
"""


def cmdline_parser():
    parser = argparse.ArgumentParser(
        description='Split Sentinel-1 TOPS file and apply orbit using SNAP.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('zip_dir', help='Sentinel-1 TOPS zips directory')
    parser.add_argument('output_dir', help='output slc directory')
    parser.add_argument('info_file',
                        help='file including date IW first_burst last_burst')
    inps = parser.parse_args()

    return inps


if __name__ == "__main__":
    # get inputs
    inps = cmdline_parser()
    zip_dir = os.path.abspath(inps.zip_dir)
    output_dir = os.path.abspath(inps.output_dir)
    info_file = os.path.abspath(inps.info_file)

    # check inputs
    if not os.path.isdir(zip_dir):
        sys.exit(f"Error, {zip_dir} does not exist.")

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    if not os.path.isfile(info_file):
        sys.exit(f'Cannot find file {info_file}.')

    xml_dir = os.path.join(output_dir, 'xml')
    if not os.path.isdir(xml_dir):
      os.mkdir(xml_dir)

    # get slc infos
    slc_infos = []
    with open(info_file, 'r') as f:
        for line in f.readlines():
            if re.search(r'\d{8}', line) and not line.startswith('#'):
                slc_infos.append(line.strip().split())

    if len(slc_infos) == 0:
        sys.exit(f"No slc infos in {info_file}")

    # split and apply orbit
    for slc_info in slc_infos:
        date, iw, first_burst, last_burst = slc_info

        zip_files = glob.glob(os.path.join(zip_dir, f"S1*{date}*.zip"))

        index = slc_infos.index(slc_info) + 1
        print(f"\n[{index}/{len(slc_infos)}] SLC for IW{iw}: {date}\n")

        output_name = date + '_IW' + iw + '.dim'
        output_path = os.path.join(output_dir, output_name)

        if len(zip_files) == 1:
            xml_data = SPLIT_ORBIT_XML
            xml_data = xml_data.replace('IW', 'IW' + iw)
            xml_data = xml_data.replace('INPUTFILE', zip_files[0])
            xml_data = xml_data.replace('OUTPUTFILE', output_path)
            xml_data = xml_data.replace('FIRSTBURST', first_burst)
            xml_data = xml_data.replace('LASTBURST', last_burst)

            xml_path = os.path.join(xml_dir, date + '_split_orbit.xml')
        else:
            file_list = ','.join(zip_files)
            xml_data = ASSEMBLY_SPLIT_ORBIT_XML
            xml_data = xml_data.replace('IW', 'IW' + iw)
            xml_data = xml_data.replace('FILELIST', file_list)
            xml_data = xml_data.replace('OUTPUTFILE', output_path)
            xml_data = xml_data.replace('FIRSTBURST', first_burst)
            xml_data = xml_data.replace('LASTBURST', last_burst)

            xml_path = os.path.join(xml_dir,
                                    date + '_assembly_split_orbit.xml')

        with open(xml_path, 'w+') as f:
            f.write(xml_data)

        args = ["gpt", xml_path]
        process = subprocess.Popen(args,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)

        time_start = time.time()

        stdout = process.communicate()[0]
        print(str(stdout, encoding='utf-8'))

        time_delta = time.time() - time_start
        print('Finished in {} seconds.\n'.format(time_delta))

        if process.returncode != 0:
            print('Error processing {}.\n'.format(date))
        else:
            print('Processing {} completed.\n'.format(date))
