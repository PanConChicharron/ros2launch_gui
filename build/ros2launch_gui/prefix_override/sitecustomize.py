import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/arjunram/Workspace/ros2launch_gui/install/ros2launch_gui'
