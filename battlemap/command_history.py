"""Command history for undo/redo operations.

Implements the Command pattern for reversible operations.
"""


class Command:
    """Base command class."""
    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError


class AddAssetCommand(Command):
    """Command for adding an asset."""
    def __init__(self, canvas_area, asset):
        self.canvas_area = canvas_area
        self.asset = asset
        self.asset_data = asset.to_dict()

    def execute(self):
        # Asset already added, just select it
        if self.asset in self.canvas_area.assets_layer.children:
            self.canvas_area._handle_asset_select(self.asset)

    def undo(self):
        self.canvas_area.remove_asset(self.asset)


class RemoveAssetCommand(Command):
    """Command for removing an asset."""
    def __init__(self, canvas_area, asset):
        self.canvas_area = canvas_area
        self.asset = asset
        self.asset_data = asset.to_dict()

    def execute(self):
        self.canvas_area.remove_asset(self.asset)

    def undo(self):
        self.asset = self.canvas_area.restore_asset(self.asset_data)


class MoveAssetCommand(Command):
    """Command for moving an asset."""
    def __init__(self, asset, old_pos, new_pos):
        self.asset = asset
        self.old_pos = old_pos
        self.new_pos = new_pos

    def execute(self):
        self.asset.pos = self.new_pos

    def undo(self):
        self.asset.pos = self.old_pos


class RotateAssetCommand(Command):
    """Command for rotating an asset."""
    def __init__(self, asset, old_rotation, new_rotation):
        self.asset = asset
        self.old_rotation = old_rotation
        self.new_rotation = new_rotation

    def execute(self):
        self.asset.rotation = self.new_rotation

    def undo(self):
        self.asset.rotation = self.old_rotation


class ScaleAssetCommand(Command):
    """Command for scaling an asset."""
    def __init__(self, asset, old_scale, new_scale):
        self.asset = asset
        self.old_scale = old_scale
        self.new_scale = new_scale

    def execute(self):
        self.asset.scale = self.new_scale

    def undo(self):
        self.asset.scale = self.old_scale


class SetLabelCommand(Command):
    """Command for setting asset label."""
    def __init__(self, asset, old_label, new_label):
        self.asset = asset
        self.old_label = old_label
        self.new_label = new_label

    def execute(self):
        self.asset.label_text = self.new_label

    def undo(self):
        self.asset.label_text = self.old_label


class CommandHistory:
    """Manages command history for undo/redo."""
    def __init__(self, max_history=50):
        self.max_history = max_history
        self.history = []
        self.current_index = -1

    def execute(self, command):
        """Execute a command and add it to history."""
        command.execute()
        
        # Remove any commands after current index (redo history)
        self.history = self.history[:self.current_index + 1]
        
        # Add new command
        self.history.append(command)
        self.current_index += 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1

    def undo(self):
        """Undo the last command."""
        if self.can_undo():
            command = self.history[self.current_index]
            command.undo()
            self.current_index -= 1
            return True
        return False

    def redo(self):
        """Redo the next command."""
        if self.can_redo():
            self.current_index += 1
            command = self.history[self.current_index]
            command.execute()
            return True
        return False

    def can_undo(self):
        """Check if undo is available."""
        return self.current_index >= 0

    def can_redo(self):
        """Check if redo is available."""
        return self.current_index < len(self.history) - 1

    def clear(self):
        """Clear all history."""
        self.history = []
        self.current_index = -1
