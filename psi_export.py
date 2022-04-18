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

PSI_EXPORT_XML = """<graph id="Graph">
  <version>1.0</version>
  <node id="StampsExport">
    <operator>StampsExport</operator>
    <sources>
      <sourceProduct refid="Read"/>
      <sourceProduct.1 refid="Read(2)"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <targetFolder>OUTPUTFOLDER</targetFolder>
      <psiFormat>true</psiFormat>
    </parameters>
  </node>
  <node id="Read">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>COREG_FILE</file>
    </parameters>
  </node>
  <node id="Read(2)">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>IFG_FILE</file>
    </parameters>
  </node>
  <applicationData id="Presentation">
    <Description/>
    <node id="StampsExport">
      <displayPosition x="161.0" y="215.0"/>
    </node>
    <node id="Read">
      <displayPosition x="20.0" y="196.0"/>
    </node>
    <node id="Read(2)">
      <displayPosition x="29.0" y="237.0"/>
    </node>
  </applicationData>
</graph>

"""

EXAMPLE = """Example:
  python3 psi_export.py /ly/coreg /ly/ifg ly/InSAR_20221229
"""


def cmdline_parser():
    parser = argparse.ArgumentParser(
        description='Export PSI files of StaMPS using SNAP.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('coreg_dir', help='input coreg directory')
    parser.add_argument('ifg_dir', help='input ifg directory')
    parser.add_argument('output_dir', help='output directory')
    inps = parser.parse_args()

    return inps


if __name__ == "__main__":
    # get inputs
    inps = cmdline_parser()
    coreg_dir = os.path.abspath(inps.coreg_dir)
    ifg_dir = os.path.abspath(inps.ifg_dir)
    output_dir = os.path.abspath(inps.output_dir)

    # check inputs
    if not os.path.isdir(coreg_dir):
        sys.exit(f"Error, {coreg_dir} does not exist.")

    if not os.path.isdir(ifg_dir):
        sys.exit(f"Error, {ifg_dir} does not exist.")

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    xml_dir = os.path.join(output_dir, 'xml')
    if not os.path.isdir(xml_dir):
      os.mkdir(xml_dir)

    coreg_files = glob.glob(os.path.join(coreg_dir, "*.dim"))

    for coreg_file in coreg_files:
        index = coreg_files.index(coreg_file) + 1
        dim_name = os.path.basename(coreg_file)
        print(f"\n[{index}/{len(coreg_files)}] Processing file: {dim_name}\n")

        xml_data = PSI_EXPORT_XML
        xml_data = xml_data.replace('COREG_FILE', coreg_file)

        ifg_file = os.path.join(ifg_dir, dim_name)
        xml_data = xml_data.replace('IFG_FILE', ifg_file)

        xml_data = xml_data.replace('OUTPUTFOLDER', output_dir)

        xml_name = dim_name[0:-4] + '_psi_export.xml'
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
            print('Error exporting {}\n'.format(dim_name))
        else:
            print('Complete PSI export of {}\n'.format(dim_name))
