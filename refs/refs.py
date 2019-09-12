#!/usr/bin/env python
# -*- coding: utf-8 -*-

#           OH MY GIRL License
#   To create a program using this source code,
#   Follow the link below to listen to the OH MY GIRL's song at least once.
#   LINK (1): https://youtu.be/RrvdjyIL0fA
#   LINK (2): https://youtu.be/QIN5_tJRiyY
#   LINK (3): https://youtu.be/udGwca1HBM4
#   LINK (4): https://youtu.be/QTD_yleCK9Y

"""
@author:    Seonho Lee
@license:   OH_MY_GIRL License
@contact:   horensic@gmail.com
"""

import io
import refs.logger as logger
from refs.error import *
from refs.refs_type import *
from datetime import datetime, timedelta

carpe_refs_log = logger.ArinLog("ReFS", level=logger.LOG_TRACE | logger.LOG_DEBUG | logger.LOG_INFO)
# carpe_refs_log = logger.CarpeLog("ReFS", level=logger.LOG_INFO)


def ReFS(vol):
    buf = vol.read(REFS_VHDR_SZ)
    vbr = dict(zip(REFS_VHDR_FILEDS, struct.unpack(REFS_VHDR_FORMAT, buf)))
    vol.read(0x3E00)  # skip

    major_version = vbr['major']
    cluster = vbr['bps'] * vbr['cpb']

    if major_version == 1:
        return ReFSv1(vol, cluster)
    elif major_version == 3:
        return ReFSv3(vol, cluster)
    else:
        raise UnknownReFSVersionError


class ReFSv1:

    def __init__(self, vol, cluster):
        self.vol = vol
        self.cluster = cluster

    def __repr__(self):
        return 'ReFS_V1'


class ReFSv3:

    def __init__(self, vol, cluster):
        self.vol = vol
        self.cluster = cluster
        self.metapage_sz = 4 * 0x400  # 4096 bytes

        self.supb = None
        self.chkp = None
        self.container_table = None
        self.object_table = None

        self.root = None
        self.fs_meta = None

    def __repr__(self):
        return 'ReFS_V3'

    def read_volume(self):
        self.supb = SuperBlock(self.vol, 0x0000001E)
        self.chkp = CheckPoint(self.vol, self.supb.primary)

        if 'Container Table' in self.chkp.reserved_page:
            container_table = self.chkp.reserved_page['Container Table']['LCNTuple']
            self.container_table = ContainerTable(self.vol, self.cluster, container_table)
        else:
            raise CheckpointKeyError('Container Table')

        if 'Object Table' in self.chkp.reserved_page:
            object_table = self.translate_lcn(self.chkp.reserved_page['Object Table']['LCNTuple'])
            self.object_table = ObjectTable(self.vol, self.cluster, object_table)
        else:
            raise CheckpointKeyError('Object Table')

    def root_dir(self):
        if self.object_table.table:
            root_obj = self.object_table.table[OID_3['Root Directory']]
            carpe_refs_log.debug("Root LCNTuple: {0}".format(root_obj['LCNTuple']))

            root_dir = self.translate_lcn(root_obj['LCNTuple'])
            carpe_refs_log.debug("Root Offset: {0}".format(root_dir))

            self.root = ReFSDirectory(self.vol, self.cluster, root_dir)
            return True

    def file_system_metadata(self):
        if self.object_table.table:
            fs_meta_obj = self.object_table.table[OID_3['File System Metadata']]
            carpe_refs_log.debug("FS Meta LCNTuple: {0}".format(fs_meta_obj['LCNTuple']))

            fs_meta = self.translate_lcn(fs_meta_obj['LCNTuple'])
            carpe_refs_log.debug("FS Meta Offset: {0}".format(fs_meta))

            self.fs_meta = ReFSDirectory(self.vol, self.cluster, fs_meta)
            return True

    def logfile_info(self):
        if self.object_table.table:
            logfile_info_obj = self.object_table.table[OID_3['Logfile Information Table']]
            carpe_refs_log.debug("Logfile Info LCNTuple: {0}".format(logfile_info_obj['LCNTuple']))

            logfile_info = self.translate_lcn(logfile_info_obj['LCNTuple'])
            carpe_refs_log.debug("Logfile Info Offset: {0}".format(logfile_info))

            self.logfile_info = LogfileInformationTable(self.vol, self.cluster, self.translate_lcn, logfile_info)
            print(self.logfile_info.children_table[0].table)
            logfile_info_lcn = self.logfile_info.children_table[0].table[1]['LOGFILE_INFO_LCN']
            return True

    def read_file(self, metadata):
        file_data = []

        carpe_refs_log.debug(f"File Directory Entry: {metadata}")

        if not metadata['data']:
            print("File is empty")
            return file_data

        if 'LCNTuple' in metadata['data']:  # Non-resident
            address = self.translate_lcn(metadata['data']['LCNTuple'])
            carpe_refs_log.debug(f"File MSB+ offset: {address}")
            refs_reg_file = ReFSRegFile(self.vol, self.cluster, address)

            for attr_data in refs_reg_file.attributes['$DATA']:
                file_lcn = int(attr_data['LCN'])
                file_offset = self.translate_lcn(file_lcn)
                # file_size = int(attr_data['file_size'])
                self.vol.seek(file_offset * self.cluster)
                file_data.append(self.vol.read(0x200))
                # self.vol.read(file_size)

            if '$ADS' in refs_reg_file.attributes:
                ads = refs_reg_file.attributes['$ADS']  # TODO: $ADS가 여러 개 들어가 있는 경우 테스트해서 처리하기
                file_data.append(ads)

        elif 'LCN' in metadata['data'][0]:  # resident

            for attr_data in metadata['data']:
                file_lcn = int(attr_data['LCN'])
                file_offset = self.translate_lcn(file_lcn)
                print(file_offset)
                # file_size
                self.vol.seek(file_offset * self.cluster)
                file_data.append(self.vol.read(0x200))
                # self.vol.read(file_size)
        else:
            raise NotImplementedError

        return file_data

    def translate_lcn(self, LCNTuple):

        carpe_refs_log.trace(f"Translate virtual LCN: <{LCNTuple}>")

        def calc_cpc_shift(cpc):
            cpc_shift = 0
            while True:
                cpc = cpc >> 1
                if cpc == 0:
                    break
                cpc_shift += 1
            return cpc_shift + 1

        cpc = self.container_table.cpc
        cpc_shift = calc_cpc_shift(cpc)

        if isinstance(LCNTuple, list):
            translated_LCNTuple = []
            for LCN in LCNTuple:
                key = LCN >> cpc_shift
                cluster_no = self.container_table.cluster_no(key)
                carpe_refs_log.trace(f"Key: {key}, Cluster No: {cluster_no}")
                LCN = LCN & (cpc - 1)
                LCN += cluster_no
                translated_LCNTuple.append(LCN)
        elif isinstance(LCNTuple, int):
            LCN = LCNTuple
            key = LCN >> cpc_shift
            cluster_no = self.container_table.cluster_no(key)
            LCN = LCN & (cpc - 1)
            LCN += cluster_no
            translated_LCNTuple = LCN
        else:
            # TODO: LCNTuple 타입 에러 만들어서 발생시키기
            raise LCNTupleTypeError

        return translated_LCNTuple

    def change_directory(self, obj):
        if self.object_table.table:
            carpe_refs_log.debug(f"cd {self.translate_lcn(obj['LCNTuple'])}")
            change_dir = self.translate_lcn(obj['LCNTuple'])
            return ReFSDirectory(self.vol, self.cluster, change_dir)


class FSMetaPage:

    def __init__(self, vol, LCN):
        metapage_sz = 0x1000
        vol.seek(LCN * metapage_sz)
        self.buf = io.BytesIO(vol.read(metapage_sz))
        self.header = dict(zip(META_HDR_3FILEDS, struct.unpack(META_HDR_3FORMAT, self.buf.read(META_HDR_3SZ))))
        self.refine(self.header)
        carpe_refs_log.debug("File System MetaPage Signature: {0}".format(self.header['signature'].decode('ascii')))

    def refine(self, fields):
        lcn_tuple = list()
        for i in range(1, 5):
            lcn_tuple.append(fields['LCN({0})'.format(i)])
            fields.pop('LCN({0})'.format(i))

        fields['LCNTuple'] = lcn_tuple


class Page:

    def __init__(self, vol, cluster, LCNTuple):
        self.rows = list()
        self.cluster = cluster
        if isinstance(LCNTuple, list):
            buf = bytes()
            for LCN in LCNTuple:
                offset = LCN * cluster
                vol.seek(offset)
                buf += vol.read(cluster)
            self.buf = io.BytesIO(buf)
            self.header = dict(zip(META_HDR_3FILEDS, struct.unpack(META_HDR_3FORMAT, self.buf.read(META_HDR_3SZ))))
            self.refine(self.header)

            if self.header['signature'] != b'MSB+':
                print(self.header)
                raise InvalidMetaPageSignatureError

            carpe_refs_log.debug("MetaPage Signature: {0}".format(self.header['signature'].decode('ascii')))
            carpe_refs_log.trace("MetaPage LCN: {0}".format(self.header['LCNTuple']))
        else:
            carpe_refs_log.warn("LCNTuple is not list")

    def parse_table_descriptor(self, attr_buf, datum):
        table_desc_size = struct.unpack('<I', attr_buf.read(4))[0]
        carpe_refs_log.trace(f"MetaPage Descriptor size: {hex(table_desc_size)}")
        attr_buf.seek(datum)
        table_desc_buf = attr_buf.read(table_desc_size)

        if table_desc_size == 0x8:
            # No Information
            pass

        if table_desc_size >= 0x28:
            self.table_descriptor = dict(zip(TABLE_DESC_3FILEDS,
                                             struct.unpack(TABLE_DESC_3FORMAT, table_desc_buf[:TABLE_DESC_3SZ])))
            self.table_descriptor['unknown_buf'] = table_desc_buf[TABLE_DESC_3SZ:]

    def parse_row(self, row_buf, datum):
        rows = list()

        row_buf.seek(datum)
        table_hdr_offset = datum + struct.unpack('<I', row_buf.read(4))[0]
        row_buf.seek(table_hdr_offset)
        table_hdr = dict(zip(TABLE_HDR_3FIELDS, struct.unpack(TABLE_HDR_3FORMAT, row_buf.read(TABLE_HDR_3SZ))))

        if table_hdr['type'] & 0x100:
            self.children = True

        array_size = int((table_hdr['array_end'] - table_hdr['array_start']) / 4)
        array_offset = table_hdr_offset + table_hdr['array_start']

        for i in range(array_size):
            row = dict()
            row_buf.seek(array_offset + i * 4)
            row_offset = table_hdr_offset + struct.unpack(ARR_ELEM_3FORMAT, row_buf.read(ARR_ELEM_3SZ))[0]

            row_buf.seek(row_offset)
            row['header'] = dict(zip(ROW_HDR_3FIELDS, struct.unpack(ROW_HDR_3FORMAT, row_buf.read(ROW_HDR_3SZ))))
            row['offset'] = row_offset

            if row['header']['len_key'] > 0:
                row_buf.seek(row_offset + row['header']['offset_key'])
                row['key'] = row_buf.read(row['header']['len_key'])

            if row['header']['len_value'] > 0:
                row_buf.seek(row_offset + row['header']['offset_value'])
                row['value'] = row_buf.read(row['header']['len_value'])

            rows.append(row)

        return rows

    def refine(self, fields):
        lcn_tuple = list()
        for i in range(1, 5):
            lcn_tuple.append(fields['LCN({0})'.format(i)])
            fields.pop('LCN({0})'.format(i))

        fields['LCNTuple'] = lcn_tuple


class BPlusTable:

    def __init__(self):
        pass

    def insert(self):
        pass


class MLog:

    def __init__(self, vol, cluster, LCN):
        if isinstance(LCN, int):
            buf = bytes()
            offset = LCN * cluster
            vol.seek(offset)
            buf += vol.read(cluster)

            self.buf = io.BytesIO(buf)
            self.header = dict(zip(LOGFILE_HDR_3FIELDS, struct.unpack(LOGFILE_HDR_3FORMAT, self.buf.read(LOGFILE_HDR_3SZ))))

            if self.header['signature'] != b'MLog':
                print(self.header)
                # MLog 에러 발생시키기
                raise NotImplementedError

            carpe_refs_log.debug("MLog Signature: {0}".format(self.header['signature'].decode('ascii')))
        else:
            carpe_refs_log.warn("LCN is not integer")


class SuperBlock(FSMetaPage):

    def __init__(self, vol, LCN):
        super(SuperBlock, self).__init__(vol, LCN)

        self.primary = 0
        self.secondary = 0

        fields = dict(zip(SUPB_3FILEDS, struct.unpack(SUPB_3FORMAT, self.buf.read(SUPB_3SZ))))
        for key in fields:
            setattr(self, key, fields[key])

    def __repr__(self):
        return 'ReFS SuperBlock'


class CheckPoint(FSMetaPage):

    def __init__(self, vol, LCN):
        super(CheckPoint, self).__init__(vol, LCN)

        fields = dict(zip(CHKP_3FILEDS, struct.unpack(CHKP_3FORMAT, self.buf.read(CHKP_3SZ))))
        for key in fields:
            setattr(self, key, fields[key])

        num_of_entries = struct.unpack('<I', self.buf.read(4))[0]

        offsets = []
        for i in range(num_of_entries):
            offsets.append(struct.unpack('<I', self.buf.read(4))[0])

        self.reserved_page = dict()
        reserved_name = ['Object Table', 'Unknown(0x21)', 'Unknown(0x20)', 'Attribute List', 'Directory Tree',
                         'Unknown(0x04)', 'Unknown(0x05)', 'Container Table', 'Container Table (dup)',
                         'Unknown(0x06)', 'Allocator Large', 'Unknown(0x0F)', 'Unknown(0x22)']

        for offset, name in zip(offsets, reserved_name):
            self.buf.seek(offset)
            carpe_refs_log.trace("CheckPoint Entry Offset: {0}".format(hex(offset).upper()))
            entry = dict(zip(CHKP_ENTRY_3FILEDS, struct.unpack(CHKP_ENTRY_3FORMAT, self.buf.read(CHKP_ENTRY_3SZ))))
            self.refine(entry)
            carpe_refs_log.trace(f"CheckPoint Entry: {entry}")


            if entry['padding'] == CHKP_ENTRY_PADDING:
                entry['padding'] = 'Zero-Padding'
            else:
                entry['padding'] = 'Non-Zero'

            self.reserved_page[name] = entry

    def __repr__(self):
        return 'ReFS CheckPoint'


class ContainerTable(Page):

    def __init__(self, vol, cluster, LCNTuple):
        super(ContainerTable, self).__init__(vol, cluster, LCNTuple)
        carpe_refs_log.trace(f"ContainerTable Class <LCNTuple: {LCNTuple}>")

        self.cpc = 0
        self.children = False
        self.children_table = dict()
        self.translate_table = dict()
        # self.rows = list()

        datum = self.buf.tell()  # Container Table's data start offset

        rows = self.parse_row(self.buf, datum)
        self.parse_table(vol, rows)

        if self.children:
            self.cpc = self.set_cpc()

    def __repr__(self):
        return 'ReFS ContainerTable'

    def refine_container_key(self, key):
        return struct.unpack('<2Q', key)[0]

    def parse_table(self, vol, rows):
        for row in rows:
            if 'value' in row:
                if 'key' in row:
                    row['key'] = self.refine_container_key(row['key'])
                else:
                    row['key'] = 0

                if self.children:
                    row['value'] = dict(zip(LCN_CHKSUM_3FIELDS, struct.unpack(LCN_CHKSUM_3FORMAT, row['value'])))
                    self.refine(row['value'])
                    self.children_table[row['key']] = ContainerTable(vol, self.cluster, row['value']['LCNTuple'])
                else:
                    row['value'] = dict(zip(CONTAINER_ROW_3FIELDS,
                                            struct.unpack(CONTAINER_ROW_3FORMAT, row['value'])))
                    self.translate_table[row['key']] = row['value']['cluster_no']
                    self.cpc = row['value']['cpc']
                    carpe_refs_log.trace(f"Container Table Row <Key: {hex(row['key'])}, "
                                        f"Cluster No: {hex(row['value']['cluster_no'])}, "
                                        f"CPC: {hex(row['value']['cpc'])}>")

    def set_cpc(self):
        cpc = 0
        for child_container_table in self.children_table.values():
            if cpc == 0:
                cpc = child_container_table.cpc
                continue

            if cpc != 0 and cpc == child_container_table.cpc:
                break
            elif cpc != 0 and cpc != child_container_table.cpc:
                # CPC values ​​appear differently in the Container Table
                raise CPCValueDoNotMatchError
        else:
            # CPC value not found
            raise CPCValueNotFoundError
        return cpc

    def cluster_no(self, key):
        if self.children:
            child_keys = self.children_table.keys()

            for child_key in child_keys:
                if child_key >= key:
                    table_key = child_key
                    break
            else:
                table_key = 0

            return self.children_table[table_key].translate_table[key]
        else:
            return self.translate_table[key]


class ObjectTable(Page):

    def __init__(self, vol, cluster, LCNTuple):
        super(ObjectTable, self).__init__(vol, cluster, LCNTuple)
        carpe_refs_log.trace(f"ObjectTable Class <LCNTuple: {LCNTuple}>")

        self.children = False
        self.children_table = dict()
        self.table = dict()
        # self.rows = list()

        datum = self.buf.tell()
        rows = self.parse_row(self.buf, datum)
        self.parse_table(vol, rows)

    def __repr__(self):
        return 'ReFS ObjectTable'

    def refine_object_key(self, key):
        return struct.unpack('16s', key)[0]

    def parse_table(self, vol, rows):
        for row in rows:
            if 'value' in row:
                if 'key' in row:
                    row['key'] = self.refine_object_key(row['key'])
                else:
                    row['key'] = 0

                if self.children:
                    row['value'] = dict(zip(LCN_CHKSUM_3FIELDS, struct.unpack(LCN_CHKSUM_3FORMAT, row['value'])))
                    self.refine(row['value'])
                    self.children_table[row['key']] = ObjectTable(vol, self.cluster, row['value']['LCNTuple'])
                else:
                    fixed = row['value'][:OBJECT_ROW_3SZ]
                    variable = row['value'][OBJECT_ROW_3SZ:]
                    object_info = dict(zip(OBJECT_ROW_3FIELDS, struct.unpack(OBJECT_ROW_3FORMAT, fixed)))
                    self.refine(object_info)
                    carpe_refs_log.trace(f"Object Table Row key: {hex(struct.unpack('<2Q', row['key'])[1])}, value: \n{object_info}")
                    object_info['variable'] = variable
                    self.table[row['key']] = object_info
                    # self.table[row['key']] = row['value']
                    # row['value'] = dict(zip(OBJECT_ROW_3FIELDS, struct.unpack(OBJECT_ROW_3FORMAT, row['value'])))


class UpcaseTable(Page):
    pass


class LogfileInformationTable(Page):

    def __init__(self, vol, cluster, func, LCNTuple):
        super(LogfileInformationTable, self).__init__(vol, cluster, LCNTuple)

        self.children = False
        self.children_table = dict()
        self.table = dict()

        datum = self.buf.tell()
        rows = self.parse_row(self.buf, datum)
        self.parse_table(vol, func, rows)

    def refine_logfile_key(self, key):
        return struct.unpack('<I', key)[0]

    def parse_table(self, vol, func, rows):
        for row in rows:
            if 'value' in row:
                if 'key' in row:
                    row['key'] = self.refine_logfile_key(row['key'])
                else:
                    # parent?
                    row['key'] = 0

                if self.children:
                    row['value'] = dict(zip(LCN_CHKSUM_3FIELDS, struct.unpack(LCN_CHKSUM_3FORMAT, row['value'])))
                    self.refine(row['value'])
                    logfile_info_lcn = func(row['value']['LCNTuple'])
                    self.children_table[row['key']] = LogfileInformationTable(vol, self.cluster, func, logfile_info_lcn)
                else:
                    if row['key'] > 0:
                        logfile_info = dict(zip(LOGFILE_INFO_ROW_3FIELDS, struct.unpack(LOGFILE_INFO_ROW_3FORMAT, row['value'])))
                        self.table[row['key']] = logfile_info


class ReFSDirectory(Page):

    def __init__(self, vol, cluster, LCNTuple):
        super(ReFSDirectory, self).__init__(vol, cluster, LCNTuple)

        self.children = False
        self.children_table = dict()
        self.table = dict()
        self.timestamp_flag = False

        datum = self.buf.tell()
        self.parse_table_descriptor(self.buf, datum)
        # if self.table_attribute['child_count'] > 0:
            # pass
        rows = self.parse_row(self.buf, datum)
        self.parse_table(vol, rows)

    def parse_table(self, vol, rows):
        for row in rows:
            carpe_refs_log.trace(f"Directory Row <Offset: {hex(row['offset'])}, "
                                 f"Length: {hex(row['header']['length'])}, "
                                 f"End: {hex(row['offset'] + row['header']['length'])}>")
            if 'value' in row:
                flag = 0
                file_type = 0
                name = None
                if 'key' in row:
                    flag, file_type = struct.unpack('<HH', row['key'][:4])
                    name = row['key'][4:]
                else:
                    row['key'] = 0

                if self.children:
                    row['value'] = dict(zip(LCN_CHKSUM_3FIELDS, struct.unpack(LCN_CHKSUM_3FORMAT, row['value'])))
                    self.refine(row['value'])
                    carpe_refs_log.trace(f"Directory Internal node <flag: {hex(flag)}, "
                                         f"file_type: {hex(file_type)}, "
                                         f"name: {name}, "
                                         f"node: {row['value']['LCNTuple']}>")
                    self.children_table[row['key']] = ReFSDirectory(vol, self.cluster, row['value']['LCNTuple'])
                else:
                    carpe_refs_log.trace(f"Entry <flag: {hex(flag)}, file_type: {hex(file_type)}, name: {name}>")
                    if flag == REFS_V3_FLAG_LIVE:
                        self.table[name.decode('utf-16')] = self.parse_entry(vol, file_type, row['value'])

                    elif flag == REFS_V3_FLAG_INDEX:
                        self.parse_index(row['value'])

                    else:
                        carpe_refs_log.debug("Unknown flag")

    def parse_entry(self, vol, file_type, value):

        def parse_file_entry(value):
            attributes = list()
            children = False
            attr_buf = io.BytesIO(value)
            table_hdr_offset = struct.unpack('<I', attr_buf.read(4))[0]  # For Entry Offset Array
            attr_buf.seek(table_hdr_offset)
            table_hdr = dict(zip(TABLE_HDR_3FIELDS, struct.unpack(TABLE_HDR_3FORMAT, attr_buf.read(TABLE_HDR_3SZ))))

            if table_hdr['type'] & 0x100:
                children = True

            array_size = int((table_hdr['array_end'] - table_hdr['array_start']) / 4)
            array_offset = table_hdr_offset + table_hdr['array_start']

            for i in range(array_size):
                attribute = dict()
                attr_buf.seek(array_offset + i * 4)
                row_offset = table_hdr_offset + struct.unpack(ARR_ELEM_3FORMAT, attr_buf.read(ARR_ELEM_3SZ))[0]

                attr_buf.seek(row_offset)
                attribute['header'] = dict(
                    zip(ROW_HDR_3FIELDS, struct.unpack(ROW_HDR_3FORMAT, attr_buf.read(ROW_HDR_3SZ))))

                if attribute['header']['len_key'] > 0:
                    attr_buf.seek(row_offset + attribute['header']['offset_key'])
                    attribute['key'] = attr_buf.read(attribute['header']['len_key'])

                if attribute['header']['len_value'] > 0:
                    attr_buf.seek(row_offset + attribute['header']['offset_value'])
                    attribute['value'] = attr_buf.read(attribute['header']['len_value'])

                attributes.append(attribute)

            return (attributes, children)

        metadata = dict()

        if file_type == REFS_V3_TYPE_REG:
            common = value[:REG_TYPE_ENTRY_3SZ]
            metadata = dict(zip(REG_TYPE_ENTRY_3FIELDS, struct.unpack(REG_TYPE_ENTRY_3FORMAT, common)))
            metadata['file_type'] = 'REG'

            attributes, children = parse_file_entry(value)

            for attribute in attributes:

                if children:  # Non-resident
                    attribute['value'] = dict(
                        zip(LCN_CHKSUM_3FIELDS, struct.unpack(LCN_CHKSUM_3FORMAT, attribute['value'])))
                    self.refine(attribute['value'])
                    metadata['data'] = attribute['value']
                else:  # resident
                    data = ReFSRegFile.parse_attribute(io.BytesIO(attribute['value']), 0)
                    metadata['data'] = data
                    # data = self.parse_row(io.BytesIO(attribute['value']), 0)
                    # TODO: $DATA 속성이 resident로 존재하는 경우 처리해주기

        elif file_type == REFS_V3_TYPE_DIR:
            metadata = dict(zip(DIR_TYPE_ENTRY_3FIELDS, struct.unpack(DIR_TYPE_ENTRY_3FORMAT, value)))
            metadata['file_type'] = 'DIR'

        else:
            carpe_refs_log.info(f"Unknown type: {hex(file_type)}")

        return metadata

    def parse_index(self, index_buffer):
        self.parse_table_descriptor(io.BytesIO(index_buffer), 0)
        rows = self.parse_row(io.BytesIO(index_buffer), 0)
        for row in rows:
            if ('value' in row) and ('key' in row):
                value_len, _, attr_type = struct.unpack('<3I', row['key'][:12])
                attr_name = row['key'][12:]

                carpe_refs_log.debug(f"Index Row <Attribute: {hex(attr_type)}, Name: {attr_name.decode('utf-16')}>")

                if attr_type == REFS_V3_ATTR_INDEX_ROOT:
                    pass
                else:
                    carpe_refs_log.debug(f"Unknown Attribute Type: {hex(attr_type)} {attr_name.decode('utf-16')}")

    def timestamp(self, fields):

        def win64le(v, bias=None):
            """
            ReFS Timestamp format
            :param v: little-endian binary data in long(integer) type (ex. 131210007740281591)
            :param bias: timezone option
            :return: YYYY-MM-DD hh:mm:ss.us
            """
            dt = "{0:x}".format(v)
            us = int(dt, 16) / 10.
            return datetime(1601, 1, 1) + timedelta(microseconds=us)

        fields['CreateTime'] = win64le(fields['CreateTime'])
        fields['AccessTime'] = win64le(fields['AccessTime'])
        fields['ModifiedTime'] = win64le(fields['ModifiedTime'])
        fields['EntryTime'] = win64le(fields['EntryTime'])

    def ls(self):
        if self.table:
            for name, metadata in self.table.items():
                carpe_refs_log.debug(f"{name} {metadata}")
                if not self.timestamp_flag:
                    self.timestamp(metadata)
                print(f"[{metadata['file_type']}] {name:<30} {metadata['ModifiedTime']}")
            self.timestamp_flag = True


class ReFSRegFile(Page):

    def __init__(self, vol, cluster, LCNTuple):
        super(ReFSRegFile, self).__init__(vol, cluster, LCNTuple)

        self.table = dict()
        self.children = False
        self.attributes = dict()

        datum = self.buf.tell()
        rows = self.parse_row(self.buf, datum)
        self.parse_table(vol, rows)

    @staticmethod
    def parse_attribute(attr_buf, datum):
        attr_data_list = list()

        table_hdr_offset = datum + struct.unpack('<I', attr_buf.read(4))[0]  # For Entry Offset Array

        attr_buf.seek(0x3C)
        file_size = datum + struct.unpack('<I', attr_buf.read(4))[0]  # HACK

        attr_buf.seek(table_hdr_offset)
        table_hdr = dict(zip(TABLE_HDR_3FIELDS, struct.unpack(TABLE_HDR_3FORMAT, attr_buf.read(TABLE_HDR_3SZ))))

        if table_hdr['type'] == 0x301:
            carpe_refs_log.info("Does $DATA attribute have a children?")
            # children = True

        array_size = int((table_hdr['array_end'] - table_hdr['array_start']) / 4)
        array_offset = table_hdr_offset + table_hdr['array_start']

        for i in range(array_size):
            attr_buf.seek(array_offset + i * 4)
            row_offset = table_hdr_offset + struct.unpack(ARR_ELEM_3FORMAT, attr_buf.read(ARR_ELEM_3SZ))[0]

            attr_buf.seek(row_offset)

            attr_data = dict(zip(REFS_ATTR_DATA_3FIELDS,
                                 struct.unpack(REFS_ATTR_DATA_3FORMAT, attr_buf.read(REFS_ATTR_DATA_3SZ))))

            attr_data['file_size'] = file_size
            attr_data_list.append(attr_data)

        return attr_data_list

    def parse_table(self, vol, rows):
        for row in rows:
            if ('value' in row) and ('key' in row):
                value_len, _, attr_type = struct.unpack('<3I', row['key'][:12])
                attr_name = row['key'][12:]

                if self.children:
                    pass

                else:
                    if attr_type == REFS_V3_ATTR_DATA:  ## 0x80
                        carpe_refs_log.debug(f"{hex(attr_type)} {attr_name.decode('utf-16')}")
                        self.attributes['$DATA'] = self.parse_attribute(io.BytesIO(row['value']), 0)
                        # TODO: 큰 사이즈의 파일 할당의 경우, 어떻게 되는지 확인하기

                    elif attr_type == REFS_V3_ATTR_ADS:  ## 0xB0
                        carpe_refs_log.debug(f"{hex(attr_type)} {attr_name.decode('utf-16')}")
                        self.attributes['$ADS'] = row['value']
                        # TODO: ADS 구조 분석 완료된 이후에 파싱 구현

                    else:
                        carpe_refs_log.debug(f"Unknown Attribute Type: {hex(attr_type)} {attr_name.decode('utf-16')}")


class Logfile(MLog):

    def __init__(self, vol, cluster, LCN):
        super(Logfile, self).__init__(vol, cluster, LCN)

        self.redo = None
