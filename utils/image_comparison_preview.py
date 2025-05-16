import tkinter as tk
from tkinter import ttk
from typing import List, Dict


class PreviewPanel:

    def __init__(self, parent):
        self.parent = parent
        self.frame = self._create_preview_frame()

        self.image_references = []

    def _create_preview_frame(self):
        preview_frame = ttk.LabelFrame(self.parent, text="プレビュー", padding=10)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.preview_canvas = tk.Canvas(preview_frame, bg="white")
        self.preview_canvas.grid(row=0, column=0, sticky="nsew")

        h_scrollbar = ttk.Scrollbar(
            preview_frame, orient=tk.HORIZONTAL, command=self.preview_canvas.xview
        )
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        v_scrollbar = ttk.Scrollbar(
            preview_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview
        )
        v_scrollbar.grid(row=0, column=1, sticky="ns")

        self.preview_canvas.configure(
            xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set
        )

        self.preview_inner_frame = ttk.Frame(self.preview_canvas)
        self.preview_canvas_window = self.preview_canvas.create_window(
            (0, 0), window=self.preview_inner_frame, anchor="nw"
        )

        self.preview_inner_frame.bind("<Configure>", self._on_preview_configure)
        self.preview_canvas.bind("<Configure>", self._on_canvas_configure)

        return preview_frame

    def _on_preview_configure(self, event):
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        width = event.width
        self.preview_canvas.itemconfig(self.preview_canvas_window, width=width)

    def clear_preview(self):
        for widget in self.preview_inner_frame.winfo_children():
            widget.destroy()
        self.image_references.clear()

    def display_images(
        self, visualizations: Dict[str, "np.ndarray"], scale_factor: float = 1.0
    ):
        import numpy as np
        from PIL import Image, ImageTk

        self.clear_preview()

        row = 0
        for true_name, vis_img in visualizations.items():

            if vis_img.min() < 0 or vis_img.max() > 1:
                vis_img = (vis_img - vis_img.min()) / (vis_img.max() - vis_img.min())

            pil_img = Image.fromarray((vis_img * 255).astype(np.uint8))

            if scale_factor != 1.0:
                new_size = (
                    int(pil_img.width * scale_factor),
                    int(pil_img.height * scale_factor),
                )
                pil_img = pil_img.resize(new_size, Image.LANCZOS)

            photo = ImageTk.PhotoImage(pil_img)

            self.image_references.append(photo)

            name_label = ttk.Label(
                self.preview_inner_frame, text=true_name, font=("Helvetica", 12, "bold")
            )
            name_label.grid(row=row, column=0, pady=(10, 0))
            row += 1

            image_label = ttk.Label(self.preview_inner_frame, image=photo)
            image_label.grid(row=row, column=0)
            row += 1

            if row < len(visualizations) * 2:
                ttk.Separator(self.preview_inner_frame, orient=tk.HORIZONTAL).grid(
                    row=row, column=0, sticky="ew", pady=10
                )
                row += 1

        self.preview_canvas.update_idletasks()
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all"))
