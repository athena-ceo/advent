# Copyright (c) 2026 Athena Decisions Systems SAS.
"""Hand-authored *enriched* per-location scene descriptions for image generation.

Each entry expands the original room text with vivid, faithful visual detail --
geology, materials, light and atmosphere -- so the (long-prompt) image model has
more to work with and the whole cave coheres. Nothing from the original is lost;
these only add. ``advent.scene.scene_subject_text`` uses an entry when present
and otherwise falls back to the room's own description. The per-style look and
"world bible" (see scene.STYLES) are layered on top, so one scene renders
differently per style while staying consistent.
"""
from __future__ import annotations

SCENE_DETAIL: dict[int, str] = {
    1: (
        "the end of a dirt road opens before a small brick building, its "
        "mortar cracked and furred with moss. dense forest of oak and pine crowds close over a floor "
        "of dappled leaf-litter. a small clear stream trickles out from beneath the building and "
        "spills down a shallow rocky gully, catching glints of daylight among ferns and damp, "
        "mineral-streaked stones."
    ),
    2: (
        "a road crests a low hill deep in the forest, its packed-earth surface worn pale and sloping "
        "gently back down the far side. tall trees rise on every hand, trunks mossy, the undergrowth "
        "thick with fern and bramble. through a gap in the high canopy, far off across the wooded "
        "valley, a small brick building stands tiny in the hazy blue distance."
    ),
    3: (
        "the interior of a small stone well house, a shelter built over a large natural spring. cool "
        "damp air hangs beneath a plain timbered roof; walls of rough masonry glisten and sweat with "
        "moisture. at the center the spring wells up dark and clear from a rocky basin, brimming and "
        "overflowing in thin bright rivulets across a worn, slick flagstone floor."
    ),
    4: (
        "a narrow valley threads through the forest, its floor cut by a lively stream tumbling and "
        "frothing along a bed of rounded rocks. mossy boulders and fern-choked banks rise on either "
        "side beneath a canopy of leaning trees. cool spray dampens the mineral-streaked stones, and "
        "fallen leaves eddy in the little clear pools between the rapids."
    ),
    5: (
        "open forest of tall straight trunks spaced across a floor of leaf-litter and low fern, soft "
        "columns of light sifting through the high canopy. to one side the ground drops away sharply "
        "into a deep wooded valley, its far slope lost among crowding foliage. still air, mossy roots "
        "and scattered weathered grey stones lie underfoot."
    ),
    6: (
        "open forest of widely spaced trees on gently rolling ground, dappled light falling through "
        "the leaves onto a carpet of moss and fallen twigs. to one side the land dips into a deep "
        "valley; nearby, the pale worn track of a road curves off among the trunks. the wood is calm "
        "and deserted, faintly hazy between the distant trees."
    ),
    7: (
        "a bare rock streambed where the whole stream gathers and plunges with a hiss into a mere "
        "two-inch slit in the stone at the foot of the channel. downstream the bed lies dry and swept "
        "clean, grey water-polished rock scored with old flow-lines. moss clings at the wet edges, "
        "and the surrounding forest presses close and shadowed."
    ),
    8: (
        "a broad twenty-foot depression scooped into the earth, its floor bare packed dirt fringed by "
        "scrubby forest. set flush into the ground is a strong steel grate bedded in a rough collar "
        "of grey concrete, its bars rust-streaked and heavy. a dry, stony streambed winds down into "
        "the hollow, empty and dust-dry in the daylight."
    ),
    9: (
        "a small rock chamber directly beneath a three-by-three steel grate set in the ceiling, "
        "through which pale daylight and drifting motes filter down onto a cobbled floor. the damp "
        "stone walls glisten faintly. a low, cramped crawl over rounded cobbles leads away inward to "
        "the west, fading quickly into deepening darkness."
    ),
    10: (
        "a long low passage where the way narrows to a crawl over rounded cobbles, the rock ceiling "
        "pressing close overhead. the cool stone is faintly damp, worn smooth by old water. at the "
        "eastern end a dim grey glow of distant daylight seeps in, while westward the passage sinks "
        "away into shadow."
    ),
    11: (
        "a cluttered chamber heaped with mud, twigs and stony debris washed down from the surface, "
        "where a low wide cobbled passage chokes off in packed silt. an awkward, tilted canyon climbs "
        "away upward to the west through rough broken rock. on one damp wall a crude marking is "
        "scrawled in rough strokes, barely legible in the gloom."
    ),
    12: (
        "an awkward canyon running east and west, its floor tilted and uneven so the rough walls lean "
        "at odd sloping angles. narrow and confining, the grey stone is fractured and damp, studded "
        "with jutting ledges. loose scree shifts underfoot, and the cramped passage climbs and drops "
        "unevenly into darkness at either end."
    ),
    13: (
        "a splendid vaulted chamber rising some thirty feet, its walls sheeted in frozen rivers of "
        "orange flowstone that gleam wet and glassy in the gloom. rippling curtains and lobes of "
        "mineral drape the rock. an awkward broken canyon opens on the east side and a good clear "
        "passage on the west, both swallowed quickly by shadow."
    ),
    14: (
        "a low passage ends at a small pit in the floor that breathes faint traces of pale white "
        "mist, curling and drifting up from the dark shaft below. the surrounding rock is cool and "
        "damp. beyond the pit the way pinches out entirely, save for a thin narrow crack in the stone "
        "leading onward into blackness."
    ),
    15: (
        "one end of a vast hall stretching away west beyond the reach of sight, dark openings gaping "
        "on either side. a wide stone staircase descends into blackness, a cold wind flowing up it. "
        "wisps of pale white mist sway to and fro through the air almost as if alive. overhead behind "
        "rises a smooth rock dome with a passage at its top."
    ),
    16: (
        "a tight fracture in the cave wall, the rock pinching down to a crack far too narrow to pass. "
        "jagged edges of grey stone frame a mere sliver of darkness beyond, streaked with mineral "
        "seep and beaded with damp. the cramped dead space is close and still, the fissure tapering "
        "away into impenetrable shadow."
    ),
    17: (
        "the east bank of a deep fissure that slices clear across the hall, the cleft too wide to "
        "leap. thick pale mist hangs heavy here, blurring the far edge and pooling over the drop. the "
        "rough stone lip is damp and crumbling, and the chasm below vanishes into cold, vaporous "
        "dark."
    ),
    18: (
        "a low, cramped room of rough grey rock, its ceiling pressing close overhead and the air "
        "still and dead. on one wall a crude hand-lettered note is scrawled in rough strokes, "
        "weathered but deliberate. shadowed recesses ring the chamber, and a flight of worn stone "
        "steps climbs away into darkness nearby."
    ),
    19: (
        "the hall of the mountain king, a broad echoing cavern of dark stone with rough passages "
        "gaping off in every direction. the vaulted ceiling is lost in gloom, the walls ribbed and "
        "streaked with mineral seep. the cold still air carries a faint drip of water, and each black "
        "opening leads away into deep silence."
    ),
    20: (
        "the rocky floor at the bottom of a deep, narrow pit, walls of fractured stone rising sheer "
        "on every side toward a small far-off patch of dark high above. loose rubble and shattered "
        "rock litter the ground. the air is cold, close and utterly silent, the sheer shaft vanishing "
        "upward into blackness."
    ),
    21: (
        "a bleak, lightless hollow deep within the cave, the shattered rock underfoot swallowed by "
        "encroaching dark. jagged walls close in on every side, cold and unyielding, streaked with "
        "damp mineral stain. no way onward shows itself; the cramped dead space holds only still air "
        "and a heavy, final silence."
    ),
    22: (
        "a great smooth rock dome curving high overhead, its sheer polished walls sweeping upward "
        "without ledge or handhold, utterly unclimbable. a faint mineral sheen glistens on the damp "
        "stone. the rounded chamber narrows to shadow far above, the vault lost in darkness, its "
        "seamless flanks rising beyond any reach."
    ),
    23: (
        "the west end of a long chamber split by two pits, standing at the brink of the near pit. a "
        "large ragged hole gapes in the wall high above this pit, opening into blackness. the "
        "surrounding rock is rough and grey, and the drop falls away steeply into shadow below."
    ),
    24: (
        "the bottom of the eastern of two pits, a rough rock-floored hollow enclosed by steep "
        "fractured walls. in one corner a small dark pool of oil lies still and glistening, its "
        "surface slick and faintly iridescent. the air is close and stale, and the pit's rim looms "
        "high overhead against deeper darkness."
    ),
    25: (
        "the bottom of the western of two pits, hemmed in by steep rough walls of grey rock. some "
        "twenty-five feet overhead a large dark hole gapes in the wall, well out of reach. loose "
        "stone litters the floor, and the shadowed shaft rises high above into gloom, the opening a "
        "black gap in the rock."
    ),
    26: (
        "the top of a deep pit where a huge leafy plant has grown its full height, thick green stalk "
        "and broad leaves reaching a ragged hole in the rock at the very top. beyond the hole a low "
        "passage opens away. damp stone frames the gap, and the shaft falls away dark below the "
        "climbing foliage."
    ),
    27: (
        "the west side of the fissure in the hall of mists, a damp rocky lip where the deep cleft "
        "cuts across the chamber. pale white mist drifts and pools over the drop, blurring the dark "
        "far bank. the rough grey walls glisten with moisture, and the chasm below fades into cold "
        "vapour and shadow."
    ),
    28: (
        "a low north-south passage of rough rock where a dark hole gapes in the floor, dropping down "
        "into an east-west passage below. the cramped ceiling presses close overhead, and the damp "
        "grey walls narrow tightly. loose stone rims the opening, and both the passage and the shaft "
        "beneath trail away into darkness."
    ),
    29: (
        "a small side chamber on the south flank of the great hall, its rough stone walls close and "
        "low. cool damp air hangs still within, the grey rock streaked with faint mineral seep and "
        "beaded with moisture. a single dim opening leads back out toward the larger cavern; the "
        "recessed space is quiet, shadowed and bare."
    ),
    30: (
        "the west side chamber of the hall of the mountain king, a rough rock room opening off the "
        "great cavern. cool still air and grey fractured walls streaked with damp enclose the space. "
        "at the far end a passage continues onward, climbing westward and upward through the stone, "
        "fading into deep shadow beyond the chamber's mouth."
    ),
    31: (
        "a small shadowed alcove of rough grey rock deep in the cave, its close walls damp and "
        "faintly glistening. on the stone face a strange crude marking has been scratched, angular "
        "and deliberate, its meaning obscure. the cramped recess is silent and still, the low ceiling "
        "pressing near, dim passages trailing off into surrounding darkness."
    ),
    32: (
        "a low, close chamber of dark rock choking a narrow passage deep in the cave, the rough walls "
        "damp and pressing near. loose stone and grit cover the uneven floor. the way onward pinches "
        "tight through the fractured stone, shadowed and silent, the cramped opening barely wide "
        "enough to squeeze past into darkness."
    ),
    33: (
        "a large chamber of grey stone with a passage opening to the south and another to the west, "
        "and a wall of broken, tumbled rock heaping up to the east. at the room's center a boulder "
        "bears a large crude marking, roughly painted in bold strokes. cool damp air and faint "
        "mineral seep fill the still, shadowed space."
    ),
    34: (
        "a chaotic jumble of tumbled rock, broken slabs and boulders wedged at every angle, cracks "
        "and narrow fissures splitting the grey stone in all directions. the cramped, uneven space "
        "offers no clear floor, only shifting scree and jagged edges. damp seeps between the "
        "fractures, and darkness pools in the countless clefts and gaps."
    ),
    35: (
        "a low rectangular window cut into rough cave rock overlooks a huge vertical pit that soars "
        "up beyond sight and drops more than fifty feet to a dim, indistinct floor; pale white mist "
        "pools across that distant bottom, thickening toward the right; faint scuffs mark the dust "
        "along the sill; directly opposite, twenty-five feet across the void, a matching window "
        "frames a warmly lit chamber; damp mineral air, cold stone."
    ),
    36: (
        "a dirty, broken subterranean passage of crumbling grey stone and grit-strewn floor; to the "
        "east the ceiling drops into a tight low crawl, while to the west the corridor opens wide "
        "into darkness; overhead a ragged hole breaks through the rock into yet another passage; "
        "loose rubble, dust-filmed walls, damp cool air and shadowed recesses."
    ),
    37: (
        "the brink of a small, clean, climbable pit sunk into smooth pale limestone, its rounded "
        "walls dropping in easy handholds to a shadowed bottom; a low crawl leads off west into "
        "darkness; the rock is dry and lightly dusted, edges worn soft, the air still and cool in "
        "this quiet underground hollow."
    ),
    38: (
        "the bottom of a small rock pit where a thin trickling stream slips in through one tiny slit "
        "in the wall and drains out through another, its narrow course glistening across the damp "
        "stone floor; moisture darkens the surrounding rock, faint mineral streaks trace the seepage, "
        "and the cramped chamber holds cool, humid, subterranean air."
    ),
    39: (
        "a large underground room heaped with dusty tumbled rocks, their surfaces filmed grey with "
        "fine sediment; a big ragged hole gapes in the floor, and cracks splinter across the walls "
        "and ceiling in every direction; a single passage leads away east; dry powdery air, muted "
        "earthen tones, deep still shadow among the fractured stone."
    ),
    40: (
        "a very low, wide crawl-passage of flat compressed rock running parallel to and just north of "
        "the great misty hall; the ceiling presses close overhead, forcing the space into a broad "
        "flattened tube; faint wisps of white mist seep in from the neighboring hall, threading the "
        "cool damp air above the dusty grey floor."
    ),
    41: (
        "the west end of a vast misty hall, where a low wide crawl continues on westward and another "
        "burrows away north; set six feet up the wall a little passage opens as a dark slot; thin "
        "white mist drifts along the stone floor, softening the tall shadowed walls in cool, damp, "
        "subterranean gloom."
    ),
    42: (
        "a maze of twisty little passages, all alike: narrow winding corridors of grey rock branching "
        "and folding back on one another with no distinguishing feature, each turn identical to the "
        "last; low uneven ceilings, close scarred walls, a dusty floor, and cool stale air pressing "
        "in through the disorienting, claustrophobic subterranean tangle."
    ),
    43: (
        "a maze of twisty little passages, all alike: cramped serpentine corridors of bare grey stone "
        "twisting away in every direction, each opening a mirror of the next with nothing to tell "
        "them apart; the walls press close, the ceiling dips low, and cool motionless air hangs over "
        "the dust-covered rock floor."
    ),
    44: (
        "a maze of twisty little passages, all alike: identical winding rock corridors branching "
        "endlessly, walls scarred and featureless, every fork indistinguishable from the last; the "
        "confined tunnels bend and double back through the dark, their low ceilings and dusty floors "
        "lit by nothing but the flat grey monotony of confusing subterranean stone."
    ),
    45: (
        "a maze of twisty little passages, all alike: a bewildering knot of narrow rock corridors "
        "curling through the dark, each passage a featureless twin of its neighbors; close grey "
        "walls, uneven low ceilings, and a fine layer of dust across the floor, the cool dead air "
        "unbroken by any landmark in the disorienting maze."
    ),
    46: (
        "a dead end: a cramped pocket of bare grey rock where the twisting passage simply stops "
        "against a blank wall of stone; the ceiling sags low and the walls close in on three sides, "
        "floor scattered with grit and dust; still, cool, silent subterranean air fills the small "
        "blind chamber."
    ),
    47: (
        "a dead end: the narrow winding corridor pinches shut against solid rock, leaving a tight "
        "blind alcove of featureless grey stone; scarred walls press in, the low ceiling drops, and a "
        "thin film of dust coats the floor; the air is cool and utterly still in the cramped, "
        "lightless recess."
    ),
    48: (
        "a dead end: the passage terminates abruptly at a wall of unbroken stone, a small cul-de-sac "
        "of rough grey rock with nowhere further to go; the ceiling hangs low, the walls crowd close, "
        "and dust lies undisturbed on the floor amid the quiet, cool, subterranean gloom."
    ),
    49: (
        "a maze of twisty little passages, all alike: winding rock corridors coiling away identically "
        "in every direction, walls bare and featureless, each junction indistinguishable from the "
        "last; the tunnels twist through the dark beneath low uneven ceilings, dust on the stone "
        "floor, cool stagnant air heavy in the confusing subterranean warren."
    ),
    50: (
        "a maze of twisty little passages, all alike: a labyrinth of cramped grey-rock corridors "
        "folding back on themselves, every passage a perfect echo of the others with no feature to "
        "distinguish it; close scarred walls, dipping low ceilings, a dusty floor, and still cool air "
        "pervading the disorienting underground tangle."
    ),
    51: (
        "a maze of twisty little passages, all alike: serpentine stone corridors branching without "
        "end, each opening identical to the next, the rock walls monotonous and unmarked; the tunnels "
        "wind through the dark under low ceilings, their floors powdered with dust, the confined air "
        "cool and motionless throughout the bewildering maze."
    ),
    52: (
        "a maze of twisty little passages, all alike: narrow twisting rock corridors curling off in "
        "every direction, indistinguishable one from another, walls featureless and close; the low "
        "ceilings press down over dust-strewn floors, and the cool dead subterranean air lies "
        "unmoving in the confusing, claustrophobic stone warren."
    ),
    53: (
        "a maze of twisty little passages, all alike: an endless coil of cramped grey corridors "
        "bending and rejoining, each fork a mirror of the last with nothing to mark it; the scarred "
        "rock walls crowd inward, the ceiling hangs low, and fine dust covers the floor in the still, "
        "cool, disorienting dark."
    ),
    54: (
        "a dead end: the twisting corridor closes against a blank face of grey stone, forming a tight "
        "blind pocket with no way onward; the low ceiling and crowding walls hem in the small space, "
        "dust lying undisturbed across the floor; cool, silent, unmoving air fills the cramped "
        "subterranean recess."
    ),
    55: (
        "a maze of twisty little passages, all alike: a disorienting weave of narrow rock corridors "
        "twisting through the dark, every passage identical to its neighbors and utterly featureless; "
        "the close grey walls, low uneven ceilings, and dust-covered floors repeat without variation "
        "in the cool, stagnant, claustrophobic underground labyrinth."
    ),
    56: (
        "a dead end: the winding passage halts at a solid wall of rough grey rock, a cramped blind "
        "alcove with nowhere further to go; the ceiling presses low, the walls close in tight, and "
        "grit and dust litter the floor; the small chamber holds only still, cool, subterranean "
        "silence."
    ),
    57: (
        "the brink of a thirty-foot pit, a massive orange stone column of glistening flowstone "
        "streaming down one wall from ceiling to floor below; the drop is climbable descending but "
        "offers no way back up; the winding maze of narrow rock corridors continues on at this upper "
        "level, cool and dim, dust on the stone underfoot."
    ),
    58: (
        "a dead end: the corridor terminates against unbroken grey rock, a tight blind pocket of "
        "featureless stone with no exit ahead; the low ceiling sags and the scarred walls crowd "
        "close, dust settled thick on the floor; cool, motionless subterranean air fills the cramped, "
        "silent recess."
    ),
    59: (
        "a very low, wide crawl-passage of flat grey rock running parallel to and just north of the "
        "great misty hall; the ceiling hangs close overhead, flattening the space into a broad "
        "shallow tube; thin tendrils of white mist drift in from the adjacent hall, hazing the cool "
        "damp air above the dusty stone floor."
    ),
    60: (
        "the east end of a very long featureless hall of bare rock stretching away without side "
        "chambers; to the east a low wide crawl slants upward into darkness, and to the north a round "
        "two-foot hole angles down through the floor; the walls run smooth and plain, the cool still "
        "air quiet in the shadowed subterranean corridor."
    ),
    61: (
        "the west end of a very long, featureless hall of plain grey stone, its smooth blank walls "
        "stretching away eastward into darkness; here the hall meets and joins a narrow north/south "
        "passage cutting across it; the ceiling is even, the floor dusty and bare, the cool "
        "subterranean air still and undisturbed."
    ),
    62: (
        "a crossover where a high, tall north/south passage intersects a low, cramped east/west one, "
        "the two corridors meeting at different levels through the grey rock; the vaulted upper slot "
        "rises overhead while the flattened lower crawl cuts beneath; scarred stone walls, dust on "
        "the floor, cool dim air in the quiet subterranean junction."
    ),
    63: (
        "a dead end: the passage closes against a blank wall of rough grey stone, a small blind "
        "alcove with no way forward; the low ceiling drops close and the walls press in, grit "
        "scattered across the dusty floor; the cramped recess holds only cool, still, silent "
        "subterranean air."
    ),
    64: (
        "a complex junction where a low hands-and-knees passage from the north meets a higher crawl "
        "from the east, the two merging into a comfortable walking passage that heads off west; "
        "overhead the rock opens into a large room; moisture beads on the grey walls and the air "
        "hangs damp and cool through the tangled subterranean crossing."
    ),
    65: (
        "bedquilt, a long east/west passage of grey rock riddled with holes everywhere, dark openings "
        "pocking the walls, floor, and low ceiling in every direction like a stitched patchwork of "
        "gaps; the winding corridor runs on into shadow, its fractured stone cool and dusty, side- "
        "holes gaping randomly into the surrounding subterranean dark."
    ),
    66: (
        "the swiss cheese room, its walls pocked and riddled with countless rounded holes so the grey "
        "stone resembles a wheel of cheese; obvious passages open away to the west, east, northeast, "
        "and northwest, and a large squared block of bedrock occupies part of the floor; cool dim "
        "air, dust underfoot, hollow shadowed cavities everywhere."
    ),
    67: (
        "the east end of the twopit room, its floor littered with thin flat rock slabs that step down "
        "easily into the pits; a path threads past the pits here, joining passages from east and "
        "west; holes pock the walls all around, the only large one gaping high on the wall directly "
        "above the western pit, out of reach; cool dim subterranean air."
    ),
    68: (
        "the slab room, a large low circular chamber whose entire floor is one immense fallen slab of "
        "rock cracked from the ceiling above; east and west, once-great passages now lie choked with "
        "tumbled boulders, while low small openings burrow north and south, the southern one quickly "
        "bending west around the boulder-fall; cool damp air, dust and shattered stone."
    ),
    69: (
        "a secret north/south canyon of narrow grey rock running high above a large room, its floor a "
        "slender ledge overlooking the dark void below; the tall fissure-walls rise close on either "
        "side, streaked with mineral seepage and worn smooth; cool damp air drifts up from the "
        "chamber beneath, and deep shadow fills the hidden cleft."
    ),
    70: (
        "a narrow secret canyon running north to south, its fluted limestone walls pressing close, "
        "cut high in the rock above a sizable passage that opens in the floor below; damp gray stone "
        "streaked with mineral rust and faint seams of calcite, cool still air, the fissure narrowing "
        "overhead into darkness, a quiet suspended cleft hanging between two levels of the cave."
    ),
    71: (
        "a junction where three secret canyons meet, one bearing north, one south, one southeast; the "
        "northern cleft soars as tall as the other two combined, its sheer limestone walls rising "
        "into shadow, while the lower two taper away; slick gray rock veined with damp mineral "
        "streaks, close still air, narrow floors of fallen scree between towering fissured walls."
    ),
    72: (
        "a broad low chamber, its ceiling pressing down close to the floor so the span reads far "
        "wider than it is high; three tight crawlways bore away into the rock to the north, "
        "southeast, and southwest; flat slabs underfoot, damp gritty limestone streaked with pale "
        "mineral bloom, cool motionless air, faint drip-marks darkening the low rock overhead."
    ),
    73: (
        "a low crawlway pinching shut into a dead end, the rock closing to a blind pocket too tight "
        "to pass; a scuffed gritty floor of packed dirt and small stones, damp gray limestone walls "
        "narrowing overhead, faint pale mineral streaks, close stale air, the passage simply ending "
        "against solid unbroken stone."
    ),
    74: (
        "a secret canyon running east to west, its fissured limestone walls fluted by old water- "
        "carving; midway it bridges over a much tighter canyon slicing across fifteen feet below, a "
        "dark slot dropping away into shadow; damp gray rock veined with rust and calcite, cool still "
        "air, a narrow ledge of stone spanning the gap between the two crossing clefts."
    ),
    75: (
        "a slightly wider pocket in an otherwise painfully tight north/south canyon, where the walls "
        "bulge apart just enough to stand before squeezing shut again above and below; smooth water- "
        "worn limestone pressing close on both sides, damp and cool, faint pale mineral streaks "
        "running vertically, the narrow slot continuing into darkness at either end."
    ),
    76: (
        "the point where a narrow canyon pinches down too tight to continue south; the fissured "
        "limestone walls converge to a thin dark slot, impassable, water-smoothed and streaked with "
        "rust-brown mineral stain; cool damp air, gritty rubble underfoot, the cleft simply squeezing "
        "shut against unbroken rock ahead while the way back opens north."
    ),
    77: (
        "a tall narrow canyon running east to west, its water-carved limestone walls soaring far "
        "overhead into darkness; low in the north wall a tight crawl bores about three feet before "
        "the rock seems to widen beyond; damp gray stone veined with calcite, cool still air, a slot "
        "of shadow marking where the cramped opening breaks into larger space."
    ),
    78: (
        "a canyon ending abruptly against a chaotic mass of tumbled boulders, huge blocks of "
        "fractured limestone heaped floor to ceiling and sealing the way completely; damp gray stone "
        "dusted with grit, jagged broken edges catching faint shadow, cool still air, the smooth "
        "canyon walls giving way to this jumbled dead-end pile of collapse."
    ),
    79: (
        "a low rock chamber where a shallow stream drains away through a pair of round foot-wide "
        "openings set low in the wall, dark throats swallowing the water; wet gray stone slick with "
        "flow, damp echoing air, mineral stain rimming the twin holes, ripples fanning across the "
        "shallow bed toward the constricted outlets in the rock."
    ),
    80: (
        "a bewildering maze of twisty little passages, all alike, low winding tubes of water-worn "
        "limestone branching and doubling back identically in every direction; smooth gray rock "
        "rounded by ancient flow, damp close air, a faint mineral sheen on the walls, shadowed "
        "openings repeating on all sides with no feature to tell one crawl from the next."
    ),
    81: (
        "a blind dead end where the passage simply stops against solid rock; damp gray limestone "
        "walls closing to an unbroken face, gritty rubble scattered underfoot, cool still air, faint "
        "pale mineral streaks, a shallow dark pocket of stone with no way onward and the way back the "
        "only exit."
    ),
    82: (
        "a cramped dead end, the narrow passage terminating at a smooth wall of unbroken limestone; "
        "cool damp air hanging still, small stones and dust on the uneven floor, faint rust-colored "
        "mineral stain streaking the close gray rock, the low ceiling sloping down to meet the blank "
        "terminal wall."
    ),
    83: (
        "another stretch of the maze of twisty little passages, all alike, indistinguishable winding "
        "tunnels of rounded limestone curling away in every direction; smooth damp gray walls worn by "
        "long-vanished water, close cool air, a dim mineral gleam, identical shadowed mouths opening "
        "on all sides with nothing to mark one from another."
    ),
    84: (
        "a confusing junction deep in the maze of twisty little passages, all alike; low rounded "
        "tubes of pale water-smoothed limestone twist off identically north, south, and every way "
        "between; a damp gritty floor, cool still air, faint calcite bloom on the curving walls, the "
        "featureless openings offering no clue which crawl leads where."
    ),
    85: (
        "a tight dead end tucked at the close of a crawl, the rock drawing together into a blind "
        "blunt pocket; damp gray limestone streaked with mineral rust, gritty dust and small fallen "
        "fragments underfoot, cool motionless air, the low walls converging to a solid unbroken face "
        "with no passage beyond."
    ),
    86: (
        "a dead end where a low passage runs out against a jumble of solid stone; cool damp air, the "
        "gray limestone walls pinching to a blank terminal face, faint pale mineral veining, "
        "scattered grit and pebbles on the floor, the rounded ceiling dipping low to seal the space "
        "with no way forward."
    ),
    87: (
        "yet another cell of the maze of twisty little passages, all alike, a knot of identical low "
        "crawls winding away through rounded gray limestone; damp cool air, smooth water-worn walls "
        "faintly sheened with mineral deposit, shadowed openings repeating in every direction, "
        "utterly featureless and impossible to tell apart."
    ),
    88: (
        "a long narrow corridor stretching west out of sight, its straight walls of pale limestone "
        "pressing close; at the eastern end a rough hole opens onto a dense profusion of green leaves "
        "crowding the gap, hinting at foliage beyond; damp cool air, a gritty floor, faint mineral "
        "streaks on the walls, the corridor dwindling into darkness westward."
    ),
    89: (
        "the bottom of a deep narrow pit with sheer smooth walls offering nothing to grip or climb; "
        "damp gray limestone rising unbroken on every side into darkness above, the round shaft cool "
        "and close, gritty earth and small stones on the floor, faint mineral streaks glistening on "
        "the encircling rock, the only way out straight up."
    ),
    90: (
        "the ragged lip of a deep pit opening in the floor of a rocky chamber, the shaft dropping "
        "away into darkness below; damp gray limestone underfoot at the crumbling rim, cool still air "
        "rising from the depths, faint mineral streaks on the surrounding walls, a low rough opening "
        "leading onward away from the edge of the drop."
    ),
    91: (
        "the top of a steep rocky incline plunging down into a large dim room below, the slope of "
        "fractured limestone too sheer to reclimb once descended; damp gray stone strewn with loose "
        "scree, cool still air, faint mineral streaking the walls, a passage leading back away to the "
        "north, the wide dark chamber yawning at the foot of the drop."
    ),
    92: (
        "an immense cavern so vast its ceiling vanishes beyond sight into blackness overhead; "
        "cavernous passages open east, north, and south into the dark; damp gray limestone walls "
        "streaked with mineral rust and pale flowstone, cool echoing air, scattered rubble across the "
        "broad floor, and on the west wall a crude scrawled marking, the space swallowing all sense "
        "of scale."
    ),
    93: (
        "a passage abruptly blocked by a fresh cave-in, a heaped rockfall of broken limestone slabs "
        "and tumbled debris sealing the way ahead; raw pale fracture-faces still sharp and dust- "
        "coated, cool damp air thick with settled grit, jagged blocks piled floor to ceiling, the "
        "smooth older walls giving way to this recent collapse of shattered stone."
    ),
    94: (
        "one end of an immense north/south passage driving away straight and vast into darkness, its "
        "high limestone walls set far apart; damp gray stone veined with mineral rust and streaks of "
        "pale flowstone, cool still air, a broad rubble-strewn floor, the great corridor dwindling to "
        "a point in the distant shadow, cathedral-like in its scale."
    ),
    95: (
        "a magnificent cavern where a rushing stream cascades over a sparkling waterfall into a "
        "roaring whirlpool that vanishes down a hole in the floor; spray mists the damp gray "
        "limestone, mineral-streaked walls glistening, water-polished rock and swirling foam, cool "
        "churning air loud with falling water, passages opening away to the south and west."
    ),
    96: (
        "a strange soft chamber where heavy draping curtains of pale flowstone sheet down the walls "
        "in folds, the floor deep with a thick pile-like layer of soft sediment, and a dense growth "
        "of green moss carpeting the ceiling; damp still air hangs muffled and quiet, muted earthy "
        "colors throughout, the whole room hushed and cushioned in soft yielding texture."
    ),
    97: (
        "the oriental room, its damp limestone walls covered with ancient faded cave drawings in "
        "ochre and charcoal, crude figures and patterns worn by ages; a gently sloping passage rises "
        "northward, another leads southeast, and a low hands-and-knees crawl bores west; cool still "
        "air, pale mineral bloom softening the pigments, the old markings ghosting across the stone."
    ),
    98: (
        "a wide path curving around the outer rim of a large cavern, the floor dropping away into a "
        "gulf of heavy white mist far below where unseen water splashes; the vapor coils upward "
        "through a fissure in the ceiling; damp gray limestone walls slick with condensation, cool "
        "clammy air, the ledge-path hugging the rock and exiting south and west."
    ),
    99: (
        "a small rocky alcove where a narrow northwest path seems to broaden a little way on; low in "
        "the east wall an extremely tight tunnel bores away, a faint eerie glow leaking from its far "
        "end; damp gray limestone pressing close, cool still air, a gritty floor, mineral-streaked "
        "walls, the cramped squeeze framing that strange distant light."
    ),
    100: (
        "a small chamber bathed in an eerie green glow that tints the damp limestone walls, its "
        "source unseen; an extremely narrow tunnel squeezes away to the west while a dark corridor "
        "opens northeast into blackness; cool still air, smooth mineral-streaked rock washed in the "
        "strange emerald light, the tight slot and the shadowed passage the room's only ways out."
    ),
    101: (
        "a small dark chamber closed on all sides but one, a single corridor leading away south; bare "
        "damp limestone walls pressing close, cool motionless air, gritty stone underfoot, faint pale "
        "mineral streaks the only markings, the room featureless and confining, shadow pooling in its "
        "corners around the lone dark opening in the south wall."
    ),
    102: (
        "an arched hall of curving stone, its ceiling sweeping up in a natural vault; a passage of "
        "old coral once climbed up and east from here but is now choked with fallen debris; damp "
        "walls tinged with the pale pitted texture of ancient reef, cool air carrying a briny smell "
        "of sea water, mineral-crusted rock and heaped rubble sealing the former way."
    ),
    103: (
        "a large room carved from banded sedimentary rock, its floor and walls studded with countless "
        "fossil shells embedded in the pale stone; a shallow passage slopes gently downward, a "
        "steeper one climbs up, and a low hands-and-knees crawl enters from the south; cool dry air, "
        "layered strata streaking the rock, the fossilized shells catching faint texture across every "
        "surface."
    ),
    104: (
        "a long corridor sloping steadily downward, its walls ragged and sharp with jagged broken "
        "edges of fractured limestone jutting inward; cool damp air, gritty rubble strewn along the "
        "tilted floor, faint mineral rust staining the harsh angular rock, the passage descending "
        "into darkness between rows of knife-like protruding stone."
    ),
    105: (
        "a small subterranean cul-de-sac roughly eight feet across, a rounded dead-end pocket of rock "
        "hollowed into the cave wall, its damp stone surfaces close on every side, mineral seams and "
        "faint water stains threading the curved walls, the floor a scatter of grit and fallen "
        "flakes, the low ceiling pressing down over a still, enclosed, air-heavy space that goes "
        "nowhere."
    ),
    106: (
        "a cramped underground anteroom opening eastward into a broad passage, with smaller cracks "
        "slanting off west and upward through the rock, fresh diggings scarring the floor and walls "
        "where crumbled stone and loose spoil lie heaped, the air gritty with rock dust, and a crude "
        "construction sign propped in the middle of the space warning of unfinished workings beyond, "
        "its lettering rough and hand-scrawled."
    ),
    107: (
        "a claustrophobic warren of twisty little passages branching in every direction, each low "
        "crooked corridor of bare rock subtly different from the last, walls kinked and irregular, "
        "floors uneven with rubble, dark openings folding back on one another in a disorienting "
        "subterranean labyrinth of cold damp stone that offers no clear way through, all shadow and "
        "confounding sameness."
    ),
    108: (
        "a bewildering dead-heart junction of the cave, witt's end, where narrow rock passages "
        "radiate away in all directions at once, a dozen black mouths gaping from the surrounding "
        "stone, the small central floor of grit and broken rock ringed by cold damp walls, every "
        "opening looking maddeningly alike, a place of total disorientation deep underground."
    ),
    109: (
        "a sheer north/south canyon about twenty-five feet across, its damp rock walls soaring "
        "smoothly upward well over a hundred feet into darkness, white mist seeping across the floor "
        "from the north, an enormous two-sided mirror suspended by unseen means far overhead, hanging "
        "parallel and midway between the walls, and a small dark window set high in each wall some "
        "fifty feet up."
    ),
    110: (
        "a low window of eroded rock overlooking a huge pit that yawns up out of sight, an indistinct "
        "floor faintly visible more than fifty feet below where white mist pools and thickens toward "
        "the left, dust around the sill scuffed with old marks, and directly across the void some "
        "twenty-five feet away a matching window opening onto a faintly lit chamber."
    ),
    111: (
        "a broad chamber where a massive stalactite hangs from the roof, its tapering banded "
        "flowstone almost reaching the floor far below, ringed with mineral drip-lines and glistening "
        "damp, the cold rock ceiling lost in shadow above and a wide drop of empty air beneath it, "
        "the surrounding walls streaked with calcite, a lone dramatic pillar of stone suspended over "
        "the depths."
    ),
    112: (
        "a little maze of twisting passages, each one different, tight crooked corridors of bare damp "
        "rock winding and doubling through the stone, low ceilings and pinched walls kinked at odd "
        "angles, floors littered with flakes and grit, dark mismatched openings leading off in "
        "confusing directions, a cramped disorienting tangle deep in the cold underground."
    ),
    113: (
        "the edge of a large underground reservoir, an opaque cloud of white mist filling the room "
        "and boiling rapidly upward, the dark lake vanishing into vapour, fed by a stream that "
        "tumbles from a hole in the wall about ten feet overhead and splashes noisily down into "
        "unseen water within the mist, damp rock walls glistening, the single passage bending away "
        "toward the south."
    ),
    114: (
        "a blunt subterranean dead end, a short passage of bare rock closing to a solid wall, damp "
        "stone hemming in the cramped space, the floor strewn with fallen flakes and grit, mineral "
        "seams streaking the close walls, the low ceiling pressing down over a still, lightless "
        "pocket of the cave that simply stops."
    ),
    115: (
        "the northeast end of an immense torchlit repository, a hall even larger than the giant room, "
        "massive torches far overhead bathing the vast space in smoky yellow light, an enormous "
        "mirror hanging flat against one wall and stretching away toward the distant far end, the "
        "floor a broad expanse of stone scattered with grit, cavernous scale fading dim and hazy into "
        "the distance."
    ),
    116: (
        "the southwest end of a vast torchlit repository, a deep empty pit sunk into the floor on one "
        "side, a large steel grate set into the ground nearby bearing a crude marking, a huge mirror "
        "stretching off toward the distant northeast, the broad stone floor littered with dust and "
        "scattered debris, smoky light fading into far dim reaches of the enormous chamber."
    ),
    117: (
        "one side of a large deep chasm, heavy white mist rising steadily from far below and "
        "swallowing all view of the opposite edge, the near lip a shelf of damp cold rock, and a "
        "southwest path breaking away from the brink into a winding rock-walled corridor that curves "
        "off into darkness, the abyss breathing pale vapour up between the walls."
    ),
    118: (
        "a long winding underground corridor sloping gently out of sight in both directions, its damp "
        "rock walls curving away into darkness ahead and behind, the floor tilting steadily, mineral "
        "streaks and old water stains threading the stone, a quiet passage of cold gray rock rising "
        "one way and descending the other, its far ends lost in shadow."
    ),
    119: (
        "a secret rock canyon deep underground, exiting to the north and to the east, its tall narrow "
        "walls of damp stone rising close on either side, the cramped floor of grit and fallen flakes "
        "threading between them, mineral seams veining the rock, two dark cleft openings leading "
        "away, a hidden slot in the cave lit only by shadow."
    ),
    120: (
        "a hidden rock canyon with exits leading north and east, narrow walls of cold damp stone "
        "pressing close and climbing into darkness, the slotted floor of rubble and grit winding "
        "between them, calcite streaks glistening on the rock, two black cleft mouths opening away, a "
        "secret concealed passage buried deep in the cave."
    ),
    121: (
        "a secret slot canyon exiting to the north and east, its tall close walls of damp rock rising "
        "sheer on both sides, the pinched floor of broken stone threading between, mineral veins and "
        "water stains marbling the surfaces, two dark openings leading off, a narrow concealed cleft "
        "hidden within the surrounding subterranean rock."
    ),
    122: (
        "the far side of the deep chasm, a shelf of cold damp rock at the brink where heavy white "
        "mist rises from the unseen depths below, obscuring the opposite edge across the void, and a "
        "northeast path leading away from the drop into darkness, the vapour drifting up the sheer "
        "face, a quiet ledge above the misted abyss."
    ),
    123: (
        "a long straight east/west corridor of bare rock running out of sight in both directions, its "
        "damp gray walls close and even, floor scattered with grit, a faint distant rumbling carrying "
        "through the stone from somewhere far off, the cold air still, the passage stretching away "
        "into darkness at either end deep within the cave."
    ),
    124: (
        "a forking junction in a rock path, the main corridor entering from the west, the left fork "
        "bending away northeast where a dull rumbling seems to grow louder, the right fork sloping "
        "gently down to the southeast, the damp stone walls parting around the split, the floor worn "
        "and gritty, dark openings leading off into the underground."
    ),
    125: (
        "a warm-walled junction deep underground where the rock is noticeably hot to the touch, a "
        "steady thunderous roar carrying from the north loud enough to set the whole cave trembling, "
        "another passage leading away south and a low cramped crawl opening east, the damp stone "
        "faintly steaming, the air heavy and charged near the unseen source of the roar."
    ),
    126: (
        "the edge of a breathtaking view over an active volcano far below, great gouts of molten lava "
        "surging up and cascading back into the depths, glowing rock filling the cavern with a blood- "
        "red glare, sparks of ash flickering in brimstone-heavy air, myriad twisted white alabaster "
        "formations embedded in the jagged roof overhead, a devil-crafted gorge with a river of fire "
        "plunging into a bottomless pit at left, and a blistering steam geyser erupting from a barren "
        "island in a bubbling sulfurous lake at right, the far wall aflame with its own "
        "incandescence, a dark passage exiting south."
    ),
    127: (
        "a small chamber crowded with large boulders, its rock walls very warm and the trapped air "
        "almost stifling with heat, the heaped rounded stones filling much of the cramped floor, "
        "faint steam-sheen on the damp surfaces, and the only exit a low crawl heading west out of "
        "which a low ominous rumbling comes drifting, the close space heavy and oppressive."
    ),
    128: (
        "a gently sloping north/south passage lined with oddly shaped limestone formations, pale "
        "flowstone lobes and rippled mineral drapery bulging from the damp walls, curtains and knobs "
        "of calcite catching faint shadow, the smooth stone floor tilting slowly along its length, "
        "the corridor curving quietly away into darkness at both ends deep in the cave."
    ),
    129: (
        "the entrance to a large barren room, a wide dark opening in the damp rock wall, a crude sign "
        "posted above the threshold warning of a bear within, its lettering rough and hand-scrawled, "
        "the cold stone floor gritty underfoot, mineral streaks threading the surrounding rock, the "
        "empty chamber beyond swallowed in shadow past the mouth of the entrance."
    ),
    130: (
        "the interior of a large barren room, its center completely empty but for a film of gray dust "
        "across the stone floor, faint marks scuffed through the dust trailing away toward the far "
        "end, cold damp rock walls closing around the vacant space, the low ceiling lost in shadow, "
        "the only exit the passage back the way it came."
    ),
    131: (
        "a maze of twisting little passages, all different, crooked low corridors of bare damp rock "
        "kinking and folding through the stone, each mismatched opening leading to another unlike the "
        "last, walls irregular and pinched, floors strewn with flakes and grit, a disorienting "
        "subterranean tangle of cold gray rock winding off into confusing darkness."
    ),
    132: (
        "a little maze of twisty passages, all different, cramped winding corridors of damp rock "
        "threading and doubling through the stone, low ceilings and uneven walls kinked at odd "
        "angles, dark mismatched mouths opening every way, the gritty floor rising and dipping, a "
        "bewildering knot of cold underground stone with no two turns alike."
    ),
    133: (
        "a twisting maze of little passages, all different, narrow crooked rock corridors bending and "
        "crossing through the damp stone, each low opening subtly unlike its neighbours, walls "
        "flaking and irregular, floors littered with rubble, a confounding subterranean warren of "
        "cold gray rock coiling away into shadow in every direction."
    ),
    134: (
        "a twisting little maze of passages, all different, tight kinked corridors of bare damp rock "
        "winding through the stone, low ceilings pressing close, mismatched dark openings folding "
        "back on themselves, the gritty uneven floor threading between irregular walls, a "
        "disorienting cold underground tangle where no passage looks quite like another."
    ),
    135: (
        "a twisty little maze of passages, all different, cramped crooked rock corridors doubling and "
        "branching through the damp stone, each low mouth leading somewhere unlike the last, walls "
        "pinched and flaking, floors strewn with grit and fallen chips, a bewildering knot of cold "
        "gray subterranean rock coiling off into darkness."
    ),
    136: (
        "a twisty maze of little passages, all different, narrow winding corridors of damp rock "
        "kinking through the stone, low uneven ceilings and irregular walls, dark mismatched openings "
        "gaping in every direction, the gritty floor rising and falling underfoot, a confounding "
        "underground labyrinth of cold gray rock where every turn deceives."
    ),
    137: (
        "a little twisty maze of passages, all different, tight crooked rock corridors threading and "
        "folding through the damp stone, each low opening subtly unlike its neighbours, walls flaking "
        "and close, floors littered with rubble and grit, a disorienting cramped tangle of cold "
        "subterranean rock winding away into confusing shadow."
    ),
    138: (
        "a maze of little twisting passages, all different, narrow kinked corridors of bare damp rock "
        "coiling through the stone, low ceilings and uneven walls pressing in, dark mismatched mouths "
        "leading off unlike one another, the gritty floor bending between them, a bewildering cold "
        "underground warren with no two turns the same."
    ),
    139: (
        "a maze of little twisty passages, all different, cramped crooked rock corridors winding and "
        "crossing through the damp stone, each low dark opening unlike the last, walls irregular and "
        "flaking, floors scattered with grit and stone chips, a confounding subterranean tangle of "
        "cold gray rock folding away into deceptive shadow."
    ),
    140: (
        "a cramped dead end where the passage simply stops against a blank wall of solid stone; damp "
        "rock closes in on all sides, the low ceiling streaked with mineral stains, the still air "
        "heavy and cool, the way back the only way out"
    ),
}
