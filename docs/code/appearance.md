# Appearance

`appearance.py` adopts the surface hierarchy in `F:/repo/today/src/today/tk.py`:
app, top bar, panel, control, editor, border, divider, and three text strengths.
Arcs translates navy into dark amber-brown and uses gold accents. It uses the same
clam ttk base, thin card borders, flat controls, editor padding, and contrasting
selections. Fonts and spacing distinguish titles, section headings, and metadata.

The theme is installed once on the Tk thread before widget construction. Named
styles cover ttk widgets; the Tk option database covers classic Text, Entry,
Canvas, and Toplevel surfaces, including widgets created later by authoring.
Save buttons use the primary action style. Native OS title bars and message boxes
keep their system appearance. No Today dependency or lifecycle changes are needed.
