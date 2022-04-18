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

SUBSET_RDC_XML = """<graph id="Graph">
  <version>1.0</version>
  <node id="Read">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>INPUT_FILE</file>
    </parameters>
  </node>
  <node id="Subset">
    <operator>Subset</operator>
    <sources>
      <sourceProduct refid="Read"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <sourceBands/>
      <region>POLYGON</region>
      <referenceBand/>
      <geoRegion/>
      <subSamplingX>1</subSamplingX>
      <subSamplingY>1</subSamplingY>
      <fullSwath>false</fullSwath>
      <tiePointGrids/>
      <copyMetadata>true</copyMetadata>
    </parameters>
  </node>
  <node id="Write">
    <operator>Write</operator>
    <sources>
      <sourceProduct refid="Subset"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>OUTPUT_FILE</file>
      <formatName>BEAM-DIMAP</formatName>
    </parameters>
  </node>
  <applicationData id="Presentation">
    <Description/>
    <node id="Read">
            <displayPosition x="37.0" y="134.0"/>
    </node>
    <node id="Subset">
      <displayPosition x="251.0" y="132.0"/>
    </node>
    <node id="Write">
            <displayPosition x="455.0" y="135.0"/>
    </node>
  </applicationData>
</graph>
"""

SUBSET_GEO_XML = """<graph id="Graph">
  <version>1.0</version>
  <node id="Read">
    <operator>Read</operator>
    <sources/>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>INPUT_FILE</file>
    </parameters>
  </node>
  <node id="Subset">
    <operator>Subset</operator>
    <sources>
      <sourceProduct refid="Read"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <sourceBands/>
      <region>0,0,0,0</region>
      <referenceBand/>
      <geoRegion>POLYGON</geoRegion>
      <subSamplingX>1</subSamplingX>
      <subSamplingY>1</subSamplingY>
      <fullSwath>false</fullSwath>
      <tiePointGrids/>
      <copyMetadata>true</copyMetadata>
    </parameters>
  </node>
  <node id="Write">
    <operator>Write</operator>
    <sources>
      <sourceProduct refid="Subset"/>
    </sources>
    <parameters class="com.bc.ceres.binding.dom.XppDomElement">
      <file>OUTPUT_FILE</file>
      <formatName>BEAM-DIMAP</formatName>
    </parameters>
  </node>
  <applicationData id="Presentation">
    <Description/>
    <node id="Read">
            <displayPosition x="37.0" y="134.0"/>
    </node>
    <node id="Subset">
      <displayPosition x="251.0" y="132.0"/>
    </node>
    <node id="Write">
            <displayPosition x="455.0" y="135.0"/>
    </node>
  </applicationData>
</graph>
"""

EXAMPLE = """Example:
  python3 subset.py /ly/coreg /ly/coreg_subset geo 100 101 40 41
  python3 subset.py /ly/coreg /ly/coreg_subset rdc 1 1000 1 1000
"""


def cmdline_parser():
    parser = argparse.ArgumentParser(
        description='Product subset using SNAP.',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=EXAMPLE)

    parser.add_argument('input_dir', help='input directory for subset')
    parser.add_argument('output_dir', help='output directory')
    parser.add_argument('flag', help='region flag (geo or rdc)')
    parser.add_argument('region',
                        help='for geo: lon_min lon_max lat_min lat_max, ' +
                        'for rdc: start_x, end_x, start_y, end_y',
                        type=float,
                        nargs='+')
    inps = parser.parse_args()

    return inps


if __name__ == "__main__":
    # get inputs
    inps = cmdline_parser()
    input_dir = os.path.abspath(inps.input_dir)
    output_dir = os.path.abspath(inps.output_dir)
    flag = inps.flag.lower()
    region = inps.region

    # check inputs
    if not os.path.isdir(input_dir):
        sys.exit(f"Error, {input_dir} does not exist.")

    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    xml_dir = os.path.join(output_dir, 'xml')
    if not os.path.isdir(xml_dir):
        os.mkdir(xml_dir)

    if flag not in ['geo', 'rdc']:
        sys.exit("Error flag, please set flag to geo or rdc.")

    if len(region) != 4:
        sys.exit("Error region, region length must be equal to 4.")

    dims = glob.glob(os.path.join(input_dir, "*.dim"))
    if len(dims) == 0:
        sys.exit(f"Cannot find any dim file in {input_dir}")

    if flag == 'geo':
        LONMIN, LONMAX, LATMIN, LATMAX = region
        polygon = 'POLYGON (('+LONMIN+' '+LATMIN+','+LONMAX+' '+LATMIN+',' + \
        LONMAX+' '+LATMAX+','+LONMIN+' '+LATMAX+','+LONMIN+' '+LATMIN+'))'
        xml_data = SUBSET_GEO_XML
    else:
        polygon = f"{int(region[0])},{int(region[2])},{int(region[1])},{int(region[3])}"
        xml_data = SUBSET_RDC_XML

    xml_data = xml_data.replace('POLYGON', polygon)

    for dim in dims:
        index = dims.index(dim) + 1
        dim_name = os.path.basename(dim)
        print(f"\n[{index}/{len(dims)}] Processing file: {dim_name}\n")

        xml_data_out = xml_data
        xml_data_out = xml_data_out.replace('INPUT_FILE', dim)

        output_file = os.path.join(output_dir, dim_name)
        xml_data_out = xml_data_out.replace('OUTPUT_FILE', output_file)

        xml_name = dim_name[0:-4] + '_subset.xml'
        xml_path = os.path.join(xml_dir, xml_name)
        with open(xml_path, 'w+') as f:
            f.write(xml_data_out)

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
            print('Error subset with file {}\n'.format(dim_name))
        else:
            print('Complete subset with file {}\n'.format(dim_name))