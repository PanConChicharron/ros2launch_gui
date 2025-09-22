# ros2_gui_launcher/launch/demo_launcher.py

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # Create your standard ROS 2 nodes
    talker_node = Node(
        package='demo_nodes_cpp',
        executable='talker',
        name='demo_talker',
        output='screen'
    )

    listener_node = Node(
        package='demo_nodes_cpp',
        executable='listener',
        name='demo_listener',
        output='screen'
    )

    # LaunchDescription with the GUI action included
    return LaunchDescription([
        talker_node,
        listener_node,
    ])
