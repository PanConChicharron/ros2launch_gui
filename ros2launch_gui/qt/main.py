import asyncio

from launch.actions import EmitEvent
from launch.events.process import SignalProcess
from launch_ros.actions import Node

import signal

from python_qt_binding.QtCore import Qt
from python_qt_binding.QtGui import QPalette, QColor
from python_qt_binding.QtWidgets import QApplication
from python_qt_binding.QtWidgets import QMainWindow
from python_qt_binding.QtWidgets import QHBoxLayout
from python_qt_binding.QtWidgets import QPushButton
from python_qt_binding.QtWidgets import QVBoxLayout
from python_qt_binding.QtWidgets import QWidget
from python_qt_binding.QtWidgets import QHeaderView

from ..api import UserInterface as UserInterfaceBase

from launch import LaunchDescription
from launch.actions import OpaqueCoroutine

from .details_widget import DetailsWidget
from .launch_description_widget import LaunchDescriptionWidget


class MainWindow(QMainWindow):
    def __init__(self, ui: 'UserInterface'=None):
        super().__init__()

        # Enable high DPI scaling
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        self._ui = ui
        self.setWindowTitle("ROS 2 Launch GUI")
        self.launch_description_widget = LaunchDescriptionWidget(ui, self)
        header = self.launch_description_widget.tree.header()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.details_widget = DetailsWidget(self)

        # Buttons for process control
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        # Layout container for splitter + buttons
        container_layout = QVBoxLayout()
        container_layout.addWidget(self.launch_description_widget)
        container_layout.addLayout(button_layout)
        container_layout.addWidget(self.details_widget)

        container = QWidget()
        container.setLayout(container_layout)
        self.setCentralWidget(container)

        # Track selected process
        self.selected_process_item = None
        self.launch_description_widget.tree.currentItemChanged.connect(self.on_item_selected)

        # Connect buttons
        self.start_button.clicked.connect(self.start_selected_process)
        self.stop_button.clicked.connect(self.stop_selected_process)
        self.start_button.setStyleSheet("QPushButton { color: gray; }")
        self.stop_button.setStyleSheet("QPushButton { color: gray; }")
        self.show()

    def on_process_started(self, action, process_name, pid):
        self.details_widget.on_process_started(process_name, pid)
        self.launch_description_widget.on_entity_process_started(action, process_name, pid, lambda: self.details_widget.show_process_output(process_name))

    def on_process_exited(self, action, process_name, pid, return_code):
        self.details_widget.on_process_exited(process_name, return_code)
        self.launch_description_widget.on_entity_process_exited(action, process_name, pid, return_code)

    def on_process_io(self, process_name, text):
        self.details_widget.on_process_io(process_name, text)

    def on_describe_launch_entity(self, entity):
        self.launch_description_widget.on_describe_launch_entity(entity)

    def on_execution_complete(self, entity):
        self.launch_description_widget.on_execution_complete(entity)

    def on_state_transition(self, entity, start_state, goal_state):
        self.launch_description_widget.on_state_transition(entity, start_state, goal_state)

    def on_item_selected(self, current, previous):
        self.selected_process_item = current
        if current is None:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.start_button.setStyleSheet("QPushButton { color: gray; }")
            self.stop_button.setStyleSheet("QPushButton { color: gray; }")
            return

        status = current.text(1)

        if "running" in status:
            self.start_button.setEnabled(False)
            self.start_button.setStyleSheet("QPushButton { color: gray; }")
            self.stop_button.setEnabled(True)
            self.stop_button.setStyleSheet("QPushButton { color: white; }")
        elif "exit" in status or status == "":
            self.start_button.setEnabled(True)
            self.start_button.setStyleSheet("QPushButton { color: white; }")
            self.stop_button.setEnabled(False)
            self.stop_button.setStyleSheet("QPushButton { color: gray; }")
        else:
            # Lifecycle node or unknown
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(True)
        
        self.details_widget.show_process_output(current.text(0))
    
    def start_selected_process(self):
        if not self.selected_process_item:
            return
        process_name = self.selected_process_item.text(0)
        if self._ui:
            self._ui.start_process_by_name(process_name)
        
        self.start_button.setEnabled(False)
        self.start_button.setStyleSheet("QPushButton { color: gray; }")
        self.stop_button.setEnabled(True)
        self.stop_button.setStyleSheet("QPushButton { color: white; }")

    def stop_selected_process(self):
        if not self.selected_process_item:
            return
        process_name = self.selected_process_item.text(0)
        if self._ui:
            self._ui.stop_process_by_name(process_name)
        
        self.start_button.setEnabled(True)
        self.start_button.setStyleSheet("QPushButton { color: white; }")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("QPushButton { color: gray; }")

    def closeEvent(self, event):
        if self._ui is not None:
            self._ui.on_close()
        event.accept()

class UserInterface(UserInterfaceBase):
    def __init__(
            self,
            launch_description: LaunchDescription,
            debug: bool = False,
           
    ):
        super().__init__(launch_description, debug)

        self.closing = False

        self.app = QApplication([])
        self.app.setStyle("Fusion")
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.app.setPalette(dark_palette)

        self.main_window = MainWindow(self)
        self.main_window.resize(1280, 720)
        self.main_window.show()

        self.add_pending_action(OpaqueCoroutine(coroutine=self.run_qt))
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, self.handle_sigint)

    def handle_sigint(self):
        print("Caught Ctrl+C, shutting down…")
        self.on_close()
        self.app.quit()

    async def run_qt(self, *args, **kwargs):
        while not self.closing:
            if self.close_requested:
                self.main_window.close()
            self.app.processEvents()
            await asyncio.sleep(0.05)

    def on_process_started(self, process_name, pid, action):
        self.main_window.on_process_started(action, process_name, pid)

    def on_process_exited(self, process_name, pid, action, return_code):
        self.main_window.on_process_exited(action, process_name, pid, return_code)

    def on_process_io(self, process_name, text):
        self.main_window.on_process_io(process_name, text.decode())

    def on_describe_launch_entity(self, entity):
        self.main_window.on_describe_launch_entity(entity)

    def on_execution_complete(self, entity):
        self.main_window.on_execution_complete(entity)

    def on_state_transition(self, entity, start_state, goal_state):
        self.main_window.on_state_transition(entity, start_state, goal_state)

    def start_process_by_name(self, process_name):
        info = self.main_window.launch_description_widget.process_info[process_name]
        if info and 'entity' in info:
            old_entity = info['entity'].launch_entity
            node_name = process_name.split('-')[0]

            # Clone a fresh Node with the same settings
            new_entity = Node(
                package=old_entity.node_package,
                executable=old_entity.node_executable,
                name=node_name,
                namespace=old_entity.expanded_node_namespace,
                arguments=getattr(old_entity, 'arguments', None),
                parameters=getattr(old_entity, 'parameters', None),
                remappings=getattr(old_entity, 'expanded_remapping_rules', None),
                output=getattr(old_entity, 'output', 'screen')
            )

            self.add_pending_action(new_entity)

    def stop_process_by_name(self, process_name: str):
        """Stop a running process by name."""
        if process_name in self.main_window.launch_description_widget.process_items:
            process_item = self.main_window.launch_description_widget.process_items[process_name]
            pid_text = process_item.text(3)
            if pid_text.startswith("PID: "):
                try:
                    pid = int(pid_text.split(":")[1].strip())
                except ValueError:
                    return
                self.add_pending_action(
                    EmitEvent(
                        event=SignalProcess(
                            signal_number=signal.SIGINT,
                            process_matcher=lambda action: action.process_details['pid'] == pid
                        )
                    )
                )

    def on_close(self):
        self.closing = True
        super().on_close()
        
