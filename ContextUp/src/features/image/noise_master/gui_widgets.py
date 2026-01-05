"""
Noise Master - GUI Widgets.
"""

import customtkinter as ctk


class ToggleButton(ctk.CTkButton):
    def __init__(self, master, text: str, variable: ctk.BooleanVar, command=None, **kwargs):
        self.variable = variable
        self.user_command = command
        super().__init__(
            master, text=text,
            width=len(text) * 7 + 12, height=22,
            corner_radius=4,
            font=("", 10),
            command=self._toggle,
            **kwargs
        )
        self._update_color()
        self.variable.trace_add("write", lambda *_: self._update_color())

    def _toggle(self):
        self.variable.set(not self.variable.get())
        if self.user_command:
            self.user_command()

    def _update_color(self):
        if self.variable.get():
            self.configure(fg_color="#1f6aa5", hover_color="#144870")
        else:
            self.configure(fg_color="#555555", hover_color="#666666")


class SliderWithInput(ctk.CTkFrame):
    def __init__(self, master, label: str, from_: float, to_: float,
                 value: float, command, is_int: bool = False, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.is_int = is_int
        self.command = command
        self.from_ = from_
        self.to_ = to_

        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=label, width=80, anchor="w").grid(row=0, column=0, padx=2)

        self.slider = ctk.CTkSlider(
            self, from_=from_, to=to_,
            command=self._on_slider, height=16
        )
        self.slider.set(value)
        self.slider.grid(row=0, column=1, sticky="ew", padx=5)

        self.entry_var = ctk.StringVar(value=self._format(value))
        self.entry = ctk.CTkEntry(self, textvariable=self.entry_var, width=50, height=24)
        self.entry.grid(row=0, column=2, padx=2)
        self.entry.bind("<Return>", self._on_entry)
        self.entry.bind("<FocusOut>", self._on_entry)

    def _format(self, val) -> str:
        if self.is_int:
            return str(int(round(val)))
        return f"{val:.2f}"

    def _on_slider(self, val):
        v = float(val)
        if self.is_int:
            v = int(round(v))
        self.entry_var.set(self._format(v))
        if self.command:
            self.command(v)

    def _on_entry(self, event=None):
        try:
            v = float(self.entry_var.get())
            if self.is_int:
                v = int(round(v))
            slider_v = max(self.from_, min(self.to_, v))
            self.slider.set(slider_v)
            self.entry_var.set(self._format(v))
            if self.command:
                self.command(v)
        except ValueError:
            pass


class CollapsibleSection(ctk.CTkFrame):
    def __init__(self, master, title: str, expanded: bool = True, on_toggle=None, on_reset=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.expanded = expanded
        self.title = title
        self.on_toggle = on_toggle
        self.on_reset = on_reset

        self.header = ctk.CTkButton(
            self, text=self._title_text(), anchor="w",
            fg_color="transparent", hover_color="#333",
            font=("", 11, "bold"), height=24,
            command=self.toggle
        )
        self.header.pack(fill="x")
        self.header.bind("<Double-1>", self._on_double_click)

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        if expanded:
            self.content.pack(fill="both", padx=10, pady=5)

    def _title_text(self):
        return f"{'v' if self.expanded else '>'} {self.title}"

    def _on_double_click(self, event):
        if self.on_reset:
            from tkinter import messagebox
            if messagebox.askyesno("Reset Section", f"Reset '{self.title}' to defaults?"):
                self.on_reset()

    def toggle(self):
        self.expanded = not self.expanded
        self.header.configure(text=self._title_text())
        if self.expanded:
            self.content.pack(fill="both", padx=10, pady=5)
        else:
            self.content.pack_forget()
        if self.on_toggle:
            self.on_toggle(self.expanded)


class LayerItem(ctk.CTkFrame):
    def __init__(self, master, layer: dict, index: int, callbacks: dict, selected: bool):
        bg = "#454545" if selected else "#2b2b2b"
        super().__init__(master, fg_color=bg, corner_radius=6)
        self.layer = layer
        self.index = index
        self.callbacks = callbacks
        self.expanded = False

        main_row = ctk.CTkFrame(self, fg_color="transparent")
        main_row.pack(fill="x", padx=5, pady=3)

        self.var_vis = ctk.BooleanVar(value=layer.get("visible", True))
        ctk.CTkCheckBox(
            main_row, text="", width=20, variable=self.var_vis,
            command=self._on_vis
        ).pack(side="left", padx=2)

        name = layer.get("name", "Layer")[:20]
        self.lbl_name = ctk.CTkLabel(main_row, text=name, anchor="w", font=("", 11, "bold"))
        self.lbl_name.pack(side="left", fill="x", expand=True, padx=5)

        kind = str(layer.get("layer_kind", "generator")).lower()
        kind_label = "FX" if kind == "effect" else "GEN"
        self.lbl_kind = ctk.CTkLabel(main_row, text=kind_label, text_color="gray", width=30)
        self.lbl_kind.pack(side="right", padx=4)

        self.btn_expand = ctk.CTkButton(
            main_row, text=">", width=20, height=20,
            fg_color="transparent", hover_color="#555",
            command=self._toggle
        )
        self.btn_expand.pack(side="left", padx=2)

        self.lbl_drag = ctk.CTkLabel(main_row, text="::", text_color="gray", width=20, cursor="fleur")
        self.lbl_drag.pack(side="right", padx=5)

        for w in [self, self.lbl_name, self.lbl_kind, main_row]:
            w.bind("<Button-1>", lambda e: callbacks["select"](index))
            w.bind("<Button-3>", self._show_context_menu)

        self.lbl_drag.bind("<ButtonPress-1>", self._on_drag_start)
        self.lbl_drag.bind("<B1-Motion>", self._on_drag_motion)
        self.lbl_drag.bind("<ButtonRelease-1>", self._on_drag_stop)

        self.detail_frame = ctk.CTkFrame(self, fg_color="#222")

        blend_row = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        blend_row.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(blend_row, text="Blend:", width=50, anchor="w").pack(side="left")
        self.var_blend = ctk.StringVar(value=layer.get("blend_mode", "normal"))
        ctk.CTkOptionMenu(
            blend_row, variable=self.var_blend,
            values=["normal", "add", "multiply", "overlay", "screen", "subtract", "difference"],
            width=100, height=22, command=self._on_blend
        ).pack(side="left", padx=5)

        opacity_row = ctk.CTkFrame(self.detail_frame, fg_color="transparent")
        opacity_row.pack(fill="x", padx=5, pady=3)
        ctk.CTkLabel(opacity_row, text="Opacity:", width=50, anchor="w").pack(side="left")
        self.slider_opacity = ctk.CTkSlider(
            opacity_row, from_=0, to=1, width=80, height=14,
            command=self._on_opacity
        )
        self.slider_opacity.set(layer.get("opacity", 1.0))
        self.slider_opacity.pack(side="left", padx=5)
        self.lbl_opacity = ctk.CTkLabel(opacity_row, text=f"{layer.get('opacity', 1.0):.2f}", width=35)
        self.lbl_opacity.pack(side="left")

    def _show_context_menu(self, event):
        from tkinter import Menu
        m = Menu(self, tearoff=0)
        m.add_command(label="Rename", command=lambda: self.callbacks["rename"](self.index))
        m.add_command(label="Duplicate", command=lambda: self.callbacks["duplicate"](self.index))
        m.add_separator()
        m.add_command(label="Delete", command=lambda: self.callbacks["delete"](self.index), foreground="red")
        m.tk_popup(event.x_root, event.y_root)

    def _on_drag_start(self, event):
        self.configure(fg_color="#555")
        self._drag_data = {"y": event.y}

    def _on_drag_motion(self, event):
        dy = event.y - self._drag_data["y"]
        if abs(dy) > 20:
            self.callbacks["reorder"](self.index, 1 if dy > 0 else -1)
            self._drag_data["y"] = event.y

    def _on_drag_stop(self, event):
        self.callbacks["render"]()
        self.configure(fg_color="#454545" if self.index == self.callbacks["selected_idx"]() else "#2b2b2b")

    def _toggle(self):
        self.expanded = not self.expanded
        self.btn_expand.configure(text="v" if self.expanded else ">")
        if self.expanded:
            self.detail_frame.pack(fill="x", padx=5, pady=5)
        else:
            self.detail_frame.pack_forget()

    def _on_vis(self):
        self.layer["visible"] = self.var_vis.get()
        self.callbacks["render"]()

    def _on_blend(self, val):
        self.layer["blend_mode"] = val
        self.callbacks["render"]()

    def _on_opacity(self, val):
        self.layer["opacity"] = float(val)
        self.lbl_opacity.configure(text=f"{val:.2f}")
        self.callbacks["render"]()
