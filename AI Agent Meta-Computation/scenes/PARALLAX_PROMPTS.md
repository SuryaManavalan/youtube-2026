# Parallax Foreground / Background Prompts

Two prompts per scene image. **Workflow:** pass the prompt + the original scene image
into the generator. Run the FOREGROUND prompt once and the BACKGROUND prompt once for
each image.

**Chroma key:** foreground plates use flat **bright magenta `#FF00FF`** (our scenes are
dark teal with dark clothing — black would blend into the subjects and be hard to key).
Swap "magenta" for "black" only on a case-by-case basis if a subject is itself very pink.

**Two rules baked into every prompt (do not drop them):**
1. Preserve the kept subjects' original pixels EXACTLY — same position, scale, colors,
   line art, lighting — so the two layers re-composite in perfect alignment over the original.
2. Never add, move, or restyle anything; only isolate (FG) or remove-and-inpaint (BG).

Scenes **5a** (file-tree plate) and **7a** (recap card) are flat infographics — parallax
is optional there; prompts included but see the notes.

---

## 0. COLD OPEN — auditorium

**FOREGROUND**
> Isolate ONLY these foreground elements from this image, keeping them EXACTLY as they appear (same position, scale, colors, line art, lighting): (1) the central main group of seated audience members in the front rows closest to camera, and (2) the crouching janitor with the mop on the lower right. Erase everything else and replace the entire rest of the image with a solid flat bright magenta `#FF00FF` background for chroma keying. Keep clean hard edges around the isolated people. Do not add anything. Preserve their original pixels precisely so this layer aligns perfectly when composited back over the original.

**BACKGROUND**
> Generate the background plate of this image: remove ONLY (1) the central main group of seated audience members in the front rows closest to camera, and (2) the crouching janitor with the mop on the lower right. Realistically paint back in whatever is behind them — continue the auditorium floor, the glowing floor pipes, and the rows of seats seamlessly. Everything else must stay EXACTLY the same: the stage, the presenter, the glowing brain slide, the "AI SUMMIT 2026" banner, the wall pipes, the balcony crowd, and all distant seated attendees. Do not move or restyle anything. Same scene, just with those two foreground subjects absent.

---

## 1. THE DISCLAIMER — lecture hall

**FOREGROUND**
> Isolate ONLY the people from this image, keeping them EXACTLY as they appear: (1) the robed Pepe lecturer standing at the lectern, (2) the standing shouting professor on the left, (3) the seated wojak holding the thick book in the center, (4) the arms-crossed wojak seated in the lower-right foreground, (5) the writing professor at the desk on the far right, and (6) the seated professor at the far-left desk. Erase everything else and replace the entire rest of the image with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve their original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the six people (the robed Pepe lecturer at the lectern and all five wojak/soyjak academics). Paint back in what is behind them — continue the classroom floor, the empty desks and chairs, and the lectern base. Everything else must stay EXACTLY the same: the chalkboard with the hand-drawn river/flow diagram, the desk lamp, the wall speaker, the misty air. Do not move or restyle anything. Same room, just empty of people.

---

## 2. THE FRAMING — temple → data-center hall

**FOREGROUND**
> Isolate ONLY the near, floor-level figures from this image, keeping them EXACTLY as they appear: (1) the row of seated robed rishis writing at low desks in the lower-left foreground, and (2) the standing engineers with laptops in the lower-right foreground. Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the foreground seated rishis (lower left) and the foreground standing engineers with laptops (lower right). Paint back in the stone temple floor and the data-center floor behind them so the ground is continuous. Everything else must stay EXACTLY the same: the carved stone hall on the left, the server-rack nave on the right, the vaulted fresco ceiling, the central arch and distant city, the "UNIT 734 / RACK-MET-01" racks, the glowing spirit-diagrams, and any small distant figures. Do not move or restyle anything.

---

## 3. THE FUNCTION → THE FLUID

### 3a — function factory

**FOREGROUND**
> Isolate ONLY these two workers from this image, keeping them EXACTLY as they appear: (1) the yawning line-worker in coveralls standing to the left of the machine, and (2) the worker checking a phone standing on the conveyor to the right. Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the two line-workers (the yawning one at left and the phone one at right). Paint back in the factory floor and conveyor behind them. Everything else must stay EXACTLY the same: the central black "K. CORTEX-PRESS" machine, the conveyor belts, the dim/dull input sheets and the glowing smarter output sheets, the pipes, coolant lines, and background machinery. Do not move or restyle anything.

### 3b — faucet-city

**FOREGROUND**
> Isolate ONLY the front crowd of people closest to camera from this image, keeping them EXACTLY as they appear: the near wojaks catching and pouring glowing fluid — the one pouring from a bucket into a basin of papers (left), the one pouring onto an open laptop (center), the one pouring onto a phone/spreadsheet, the trio being "baptized" waist-deep, the woman pouring into a car engine bay (right), and the mother beside the baby's crib (far right). Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the front row of foreground people catching/pouring fluid (and the objects they hold). Paint back in the street and the glowing fluid rivulets on the ground behind them. Everything else must stay EXACTLY the same: the giant faucet-tower and cathedral-refinery, the descending glowing torrent, the foggy skyline and bridge, the "EPISTEMIC POUR-POINT" and "GIGO EXPRESS" signs, and the distant background crowd. Do not move or restyle anything.

### 3c — elite mezzanine

**FOREGROUND**
> Isolate ONLY the four robed elite wojak figures reclining on the sofas from this image, keeping them EXACTLY as they appear (same poses, same red/green gold-trimmed robes). Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the four seated elite wojak figures. Paint back in the empty sofas and cushions where they sat. Everything else must stay EXACTLY the same: the marble mezzanine platform, the glowing intelligence-fluid fountain, the tea trays and pastries, the brass wheel-valves and their labels, the gothic tower behind, the pipes, the city far below, and the "INTEL-FLUID RATE… GIGO RATIO 1:1… PRIVATE SUPPLY 98%" ticker railing. Do not move or restyle anything.

---

## 4. WHAT IS AN AGENT — body shop

**FOREGROUND**
> Isolate ONLY these elements from this image, keeping them EXACTLY as they appear: (1) the three vessels on the conveyor belt (the dark empty one at left, the half-filled glowing one in the middle, the brimming/overflowing glowing one at right), (2) the two aproned technicians standing behind the belt, and (3) the surprised wojak worker at the far right. Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the three conveyor vessels, the two aproned technicians, and the surprised wojak worker at right. Paint back in the conveyor belt surface and shop floor behind them. Everything else must stay EXACTLY the same: the overhead fluid-filler funnels, the shelves of boxed "TERMINAL-MODULES / API-CABLE LOOMS / MANIPULATOR HANDS" inventory, the "INTEL-FLUID PRO" canister label, the pipes, and the distant back-room workers. Do not move or restyle anything.

---

## 4a. THE AGENT LOOP — stone server-cell

**FOREGROUND**
> Isolate ONLY these elements from this image, keeping them EXACTLY as they appear: (1) the four robed hooded figures seated at their terminals around the room, (2) the figure entering/reacting at the arched doorway, and (3) the entire glowing looping ticker-tape ribbon that runs around the walls. Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the four robed seated figures, the doorway figure, and the glowing looping tape ribbon. Paint back in the desks, terminals, chairs, stone walls, and floor behind them so the round room is continuous and empty. Everything else must stay EXACTLY the same: the circular stone masonry, the arched wooden door, the wall conduits, the spilled glowing canister and tools on the floor. Do not move or restyle anything.

---

## 4b. TOOLS & FRAMEWORKS — control booth

**FOREGROUND**
> Isolate ONLY the intelligence operator from this image, keeping it EXACTLY as it appears: the glowing fluid-bodied hooded Pepe figure seated in the chair AND all of its extending glowing tool-arms reaching outward (the arms ending in the terminal-tap, the folder hand, the pointing hand, the magnifying glass, and the rm-rf lever hand). Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the seated glowing Pepe operator and its glowing tool-arms. Paint back in the console and chair behind it. Everything else must stay EXACTLY the same: the control-booth console and buttons, the wall of windows, the city/world beyond, and the tool-target panels and their labels ("RUN_BASH", "READ_FILE", "HISTORY", "SEND_EMAIL" house, "SEARCH_WEB", "RM-RF" with the panicking sysadmin). Do not move or restyle anything.

---

## 5. THE VEDIC AGENT — temple wall

**FOREGROUND**
> Isolate ONLY the free-standing people (NOT the carved wall figures) from this image, keeping them EXACTLY as they appear: (1) the robed rishi and the engineer standing together in the center, (2) the crowd of monks and Pepes gathered on the right, and (3) the backpack-wearing tourists in the lower foreground. Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the free-standing people (the central rishi + engineer, the right-side crowd, and the foreground backpackers) — but KEEP all the figures that are carved in relief into the stone wall. Paint back in the courtyard ground and wall behind the removed people. Everything else must stay EXACTLY the same: the carved layered friezes and their "CROWN / INTELLECT / EGO / REACTIVE MIND / SENSES" labels, the gopuram temple towers, the rice fields, the sky, and the glowing holographic file-tree. Do not move or restyle anything.

---

## 5a. THE FILE TREE OF THE SOUL — infographic plate

> NOTE: this is a flat 2D diagram; parallax is optional and subtle. If you want a faint
> float, split the central figure from the labels. Otherwise skip parallax for this one.

**FOREGROUND**
> Isolate ONLY the central seated meditating anatomical figure from this image, keeping it EXACTLY as it appears (same pose, same glowing chakra-nodes and channels). Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the central seated meditating figure. Keep the aged parchment background and ALL the callout labels and their thin leader-lines exactly where they are (the leader-lines may end in empty space where the figure was). Everything else must stay EXACTLY the same. Do not move or restyle anything.

---

## 5b. COULD A SOUL EMBODY IT — temple-lab ritual

**FOREGROUND**
> Isolate ONLY these elements from this image, keeping them EXACTLY as they appear: (1) the kneeling blue chakra-cyborg vessel on the central stone platform, (2) the glowing translucent human soul descending in the light-shaft above it, (3) the praying robed monks kneeling on the left, and (4) the two reacting engineers on the right (one clutching a tablet, one with hands raised). Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the kneeling cyborg vessel, the descending soul, the praying monks (left), and the two reacting engineers (right). Paint back in the stone platform, floor, and scattered offerings behind them. Everything else must stay EXACTLY the same: the temple-server hall, the carved pillars with glowing inscriptions, the server racks on both walls, the vertical shaft of light, and the cabling. Do not move or restyle anything.

---

## 6. THE AGENTIC FIELD

### 6a — sim monitor

**FOREGROUND**
> Isolate ONLY the developer and their desk from this image, keeping them EXACTLY as they appear: the headphone-wearing wojak seen from behind seated at the desk in the lower-right foreground, plus the foreground desk items (keyboard, mouse, coffee cup, papers). Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the foreground developer and their desk items. Paint back in the desk surface and wall behind them. Everything else must stay EXACTLY the same: the giant monitor, all the on-screen simulation content (the glowing settlements, entities, trade-routes, "TIME / FRAME / SETTLEMENT 14" UI, the PLAY/PAUSE/STEP controls and progress bar), the monitor bezel, and the faint reflected face in the glass. Do not move or restyle anything.

### 6b — dead → living city

**FOREGROUND**
> Isolate ONLY these elements from this image, keeping them EXACTLY as they appear: (1) the single luminous glowing agent-figure walking down the middle of the street, and (2) the front cluster of "awakened" people on the right (the kneeling praying monk, the crouching man with a laptop, and the people using the glowing API kiosks nearest camera). Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the luminous walking agent-figure and the front cluster of awakened people on the right. Paint back in the street, sidewalk, and glowing ground-veins behind them. Everything else must stay EXACTLY the same: the dead grey buildings and dark API-kiosks on the left, the awakened glowing buildings and cabling on the right, the "TERMINAL-MODULES" boxes, the skyline, the fog, and all signage. Do not move or restyle anything.

---

## 7. CLOSER

### 7a — recap taxonomy card

> NOTE: flat infographic. For a clean 2-layer parallax, float the panel strip over the
> faded backdrop. Parallax optional.

**FOREGROUND**
> Isolate ONLY the five framed thumbnail panels together with their connecting glowing arrows, their titles ("FUNCTION / FLUID / BODY / SOUL / FIELD"), and the bottom caption bar, keeping them EXACTLY as they appear. Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the five framed panels, the arrows, the titles, and the bottom caption bar. Keep and complete the faded desaturated stream-landscape backdrop so it fills the frame continuously. Everything else about the backdrop must stay EXACTLY the same (same colors, same faint figures, same light rays). Do not move or restyle anything.

### 7b — final stream

**FOREGROUND**
> Isolate ONLY the near Pepe figure from this image, keeping it EXACTLY as it appears: the backpack-wearing Pepe standing knee-deep in the water on the right, half-turned to camera with one cupped hand overflowing with glowing fluid, plus the glowing ripple/pool directly around his legs. Erase everything else and replace the rest with a solid flat bright magenta `#FF00FF` background. Keep clean hard edges. Do not add anything. Preserve original pixels precisely for perfect re-alignment.

**BACKGROUND**
> Generate the background plate: remove ONLY the near foreground Pepe figure and the ripple around his legs. Paint back in the calm glowing water surface where he stood. Everything else must stay EXACTLY the same: the endless fluid plain, the distant faucet-tower silhouette in the fog, the scattered tiny lone figures standing far off, the sky, and the ambient glow. Do not move or restyle anything.
