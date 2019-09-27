# Copyright (C) 2016-2019 4d4a5852
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "RTM Import",
    "author": "4d4a5852",
    "version": (0, 4, 0),
    "blender": (2, 80, 0),
    "location": "File -> Import",
    "description": "Import Arma 2/3 RTM files",
    "warning": "",
    "wiki_url": "https://github.com/4d4a5852/rtm_import",
    "tracker_url": "https://github.com/4d4a5852/rtm_import/issues",
    "category": "Import-Export",
    }

import struct
import bpy
import mathutils
import bpy_extras
from bpy.utils import register_class, unregister_class
import os

def read_rtm(file, verbose=False):
    signature = struct.unpack('8s', file.read(8))[0]
    if signature != b'RTM_0101':
        if signature.startswith(b'BMTR'):
            return (1, None, None, None)
        else:
            return (2, None, None, None)
    absolut_vector = struct.unpack('3f', file.read(12))
    nFrames, nBones = struct.unpack('II', file.read(8))
    if verbose:
        print('Frames:', nFrames)
        print('Bones:', nBones)
        print('absolut:', absolut_vector)
    bones = []
    frames = []
    for i in range(0, nBones):
        bones.append(struct.unpack('32s', file.read(32))[0].split(sep=b'\0',
                                                                  maxsplit=1)[0].decode().lower())
    if verbose:
        print('Bones:')
        for b in bones:
            print(b)

    for f in range(0, nFrames):
        frameTime = struct.unpack('f', file.read(4))[0]
        cur_frame = {}
        for i in range(0, nBones):
            bone = struct.unpack('32s', file.read(32))[0].split(sep=b'\0',
                                                                maxsplit=1)[0].decode().lower()
            matrix = struct.unpack('12f', file.read(48))
            cur_frame[bone] = matrix
        frames.append({'frameTime': frameTime, 'frameData': cur_frame})

    if verbose:
        print('Frames:')
        for frame in frames:
            print('Frame {}:'.format(frame['frameTime']))
            for bone, matrix in (frame['frameData']).items():
                print(bone, '\n', matrix[0:4], '\n', matrix[4:8], '\n', matrix[8:])

    return (0, absolut_vector, bones, frames)

def import_rtm(rtm, frame_start=0, set_frame_range=True, mute_bone_constraints=True, verbose=False,
               import_motion_vector=False, create_action=False):
    with open(rtm, 'rb') as file:
        result, absolut_vector, bones, frames = read_rtm(file)

    if result != 0:
        return (result, 0)

    if (import_motion_vector and hasattr(bpy.context.object, 'armaObjProps') and
        hasattr(bpy.context.object.armaObjProps, 'motionVector')):
        bpy.context.object.armaObjProps.motionVector[0] = absolut_vector[0]
        bpy.context.object.armaObjProps.motionVector[1] = absolut_vector[2]
        bpy.context.object.armaObjProps.motionVector[2] = absolut_vector[1]

    if create_action:
        new_action = bpy.data.actions.new(os.path.splitext(os.path.basename(rtm))[0])
        new_action.use_fake_user = 1
        bpy.context.object.animation_data.action = new_action

    pose = bpy.context.object.pose
    rig = bpy.context.object.data
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rootBones = [b for b in rig.bones if not b.parent]
    boneHierarchy = list(rootBones)
    for bone in rootBones:
        boneHierarchy += list(bone.children_recursive)

    if mute_bone_constraints:
        for bone in boneHierarchy:
            if bone.name.lower() in bones:
                for k, v in pose.bones[bone.name].constraints.items():
                    v.mute = True

    frame_num = frame_start
    if set_frame_range:
        bpy.context.scene.frame_start = frame_start
        bpy.context.scene.frame_end = frame_start + len(frames) - 1
    bpy.context.window_manager.progress_begin(frame_start, frame_start + len(frames) - 1)

    for frame in frames:
        bpy.context.window_manager.progress_update(frame_num)
        if verbose:
            print('Frame:', frame['frameTime'])
        bones_to_update = []
        for bone in boneHierarchy:
            if bone.name.lower() in bones:
                if verbose:
                    print(bone.name.lower(), ' found')
                m = frame['frameData'][bone.name.lower()]
                mat = mathutils.Matrix([[m[0], m[6], m[3], m[9]], [m[2], m[8], m[5], m[11]],
                                        [m[1], m[7], m[4], m[10]], [0, 0, 0, 1]])
                if bone.parent in bones_to_update:
                    depsgraph.update()
                    bones_to_update = []
                pose.bones[bone.name].matrix = mat @ bone.matrix_local
                bones_to_update.append(bone)

                pose.bones[bone.name].keyframe_insert('location', group=bone.name, frame=frame_num,
                                                      options={'INSERTKEY_NEEDED'})
                pose.bones[bone.name].keyframe_insert('rotation_quaternion', group=bone.name,
                                                      frame=frame_num, options={'INSERTKEY_NEEDED'})
                pose.bones[bone.name].keyframe_insert('scale', group=bone.name, frame=frame_num,
                                                      options={'INSERTKEY_NEEDED'})

            else:
                if verbose:
                    print(bone.name.lower(), ' not found')
        frame_num += 1
        depsgraph.update()
    bpy.context.window_manager.progress_end()
    return (0, len(frames), bpy.context.object.animation_data.action.name)

class RTMIMPORT_OT_RtmImport(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "rtmimport.rtmimport"
    bl_label = "Import RTM"
    bl_description = "Import RTM"
    filter_glob: bpy.props.StringProperty(
        default="*.rtm",
        options={'HIDDEN'})
    filename_ext = ".rtm"
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)

    frame_start: bpy.props.IntProperty(
        name="Start Frame",
        description="Starting frame in the timeline for the animation import",
        default=0)
    set_frame_range: bpy.props.BoolProperty(
        name="Set Frame Range",
        description="Set first and final frame of the playback/rendering range",
        default=True)
    mute_bone_constraints: bpy.props.BoolProperty(
        name="Disable Bone Constraints (RECOMMEND!)",
        description="Disable all bone constraints on the armature",
        default=True)
    import_motion_vector: bpy.props.BoolProperty(
        name="Import motion vector",
        description="Import motion vector from RTM (for export with Arma Toolbox)",
        default=True)
    create_action: bpy.props.BoolProperty(
        name="Create Action",
        description="Create new action and switch to it - name is based on the filename",
        default=False)

    def execute(self, context):
        files = [self.filepath]
        if self.create_action:
            folder = os.path.dirname(self.filepath)
            files = [os.path.join(folder, f.name) for f in self.files]
        for f in files:
            result, nFrames, action = import_rtm(f, frame_start=self.frame_start,
                                                 set_frame_range=self.set_frame_range,
                                                 mute_bone_constraints=self.mute_bone_constraints,
                                                 import_motion_vector=self.import_motion_vector,
                                                 create_action=self.create_action)
            if result == 0:
                self.report({'INFO'}, "{} frames imported to action {}".format(nFrames, action))
            elif result == 1:
                self.report({'ERROR'}, "Binary RTMs are not supported")
            elif result == 2:
                self.report({'ERROR'}, "Unknown/Unsupported file format")
            elif result != 0:
                self.report({'ERROR'}, "Unknown Error")
        return {'FINISHED'}

def RtmImportMenuFunc(self, context):
    self.layout.operator(RTMIMPORT_OT_RtmImport.bl_idname, text="Arma 2/3 RTM (.rtm)")

classes = (
    RTMIMPORT_OT_RtmImport,
    )

def register():
    for cls in classes:
        register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(RtmImportMenuFunc)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(RtmImportMenuFunc)
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == '__main__':
    register()
