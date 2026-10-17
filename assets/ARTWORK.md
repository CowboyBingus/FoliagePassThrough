# Artwork

Files: [banner](banner.png) (1300×372, the Nexus mod-page header size) · [square cover](thumbnail.png) (1254×1254, shown by Arsenal and HD2MM).

Drawn in code with Claude Opus 5.5 (Pillow and NumPy); no image generator was used. `source/` re-renders both PNGs pixel for pixel:

```
cd source
python art.py
```

- Same system as the Bingus Shared Loader, Mod Bindings Menu, Vanilla Plus Megapack and Sound Systems Rebalanced art (`artlib.py` and `style.py` are byte-identical copies): Franklin Gothic Heavy for the title, Bahnschrift SemiBold (width 87) for everything else, ground `#121110`, cream `#f0e8d6`, yellow `#fdd00c`.
- The hero is a tree and a bush in side view. A finned bomb fell straight through the tree's canopy (a dashed yellow trail down through the leaves, clear of the trunk and both limbs) and explodes on the ground, its starburst clear of the trunk; a rocket flew level through the low, flat-based bush and keeps going. The banner's header and the cover's side text say the same two things: "explosives fly through leaves", "trunks still stop them".
- On Nexus the page's title, stats and a darkening gradient cover the header's lower part, so the scene ends above y≈190 and the panel starts clear of the title's slashes.- The PNGs carry no metadata chunks.
