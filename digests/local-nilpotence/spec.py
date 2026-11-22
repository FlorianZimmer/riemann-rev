"""Deformalization 2: local nilpotence over a cyclotomic tower. Read by scripts/build_digest.py.

The note treats one part of its unit of the archive (Kummer theory and local nilpotence): the modules of
characters, the action by conjugation, and local nilpotence. The other members of the unit are assigned, by
source file, to the subjects of the notes to come (ELSEWHERE)."""

AV = "Development/AutomorphicArithmetic/AutomorphicVarieties/"
K = AV + "GaloisLibrary/KummerTheory/"
ST = AV + "GaloisLibrary/SelmerTransport/"
DIRECTORY = K

# key, name shown, file, word that opens the declaration, name as written at its head
DECLS = [
    # the modules of characters and the action (members of the unit)
    ("XDual", "Kum.XDual", K + "Mk0IdMapCongr.lean", "def", "XDual"),
    ("Dinf", "Kum.Dinf", K + "Mk0IdMapCongr.lean", "abbrev", "Dinf"),
    ("Xinf", "Kum.Xinf", K + "Mk0IdMapCongr.lean", "abbrev", "Xinf"),
    ("funRep", "Kum.funRep", K + "Mk0IdMapCongr.lean", "def", "funRep"),
    ("conjCond", "Kum.conjCond", K + "Mk0IdMapCongr.lean", "def", "conjCond"),
    ("EqHom", "Kum.EqHom", K + "Mk0IdMapCongr.lean", "def", "EqHom"),
    ("Un", "Kum.Un", K + "Mk0IdMapCongr.lean", "abbrev", "Un"),
    ("funRepMem", "Kum.funRepMem", K + "FunRepMem.lean", "theorem", "UpperTheory.V.Kum.funRepMem"),
    # local nilpotence (members of the unit)
    ("memPrinc", "mem_princ_iff_pow_dvd_sub_one", K + "DinfNil.lean", "private theorem", "mem_princ_iff_pow_dvd_sub_one"),
    ("powSucc", "pow_succ_dvd_pow_prime_sub_one", K + "DinfNil.lean", "private theorem", "pow_succ_dvd_pow_prime_sub_one"),
    ("qzTors", "exists_prime_pow_smul_eq_zero_qz", K + "DinfNil.lean", "private theorem", "exists_prime_pow_smul_eq_zero_qz"),
    ("princNhds", "exists_princ_subset_of_mem_nhds_one", K + "DinfNil.lean", "private theorem",
     "exists_princ_subset_of_mem_nhds_one"),
    ("dinfNil", "Kum.dinfNil", K + "DinfNil.lean", "theorem", "UpperTheory.V.Kum.dinfNil"),
    # what the statements use from outside the unit
    ("G", "G", "Formalism/ConjugateSelfDual/Statement.lean", "abbrev", "G"),
    ("QZ", "QZ", "Formalism/GaloisCohomology/Statement.lean", "def", "QZ"),
    ("cycZ", "Gal.cycZ", "ReciprocityTheory/GaloisValuations/Global.lean", "def", "cycZ"),
    ("Dec", "Gal.Dec", "ReciprocityTheory/GaloisValuations/Global.lean", "def", "Dec"),
    ("Ine", "Gal.Ine", "ReciprocityTheory/GaloisValuations/Global.lean", "def", "Ine"),
    ("princ", "princ", "Development/AutomorphicArithmetic/CyclotomicBounds/ClassNumberBounds/TotallyRealRoots/LeNuIffPowMemPrinc.lean",
     "noncomputable def", "princ"),
    ("levU", "Base.levU", ST + "ConjStableShaFam.lean", "def", "levU"),
    ("cycU", "Base.cycU", ST + "ConjStableShaFam.lean", "def", "cycU"),
    ("conjHom", "Base.conjHom", ST + "RestrictionMemInvariantH1.lean", "def", "conjHom"),
    ("conjDec", "conjGal_mem_Dec", AV + "PartsConj.lean", "theorem", "conjGal_mem_Dec"),
    ("conjIne", "conjGal_mem_Ine", AV + "PartsConj.lean", "theorem", "conjGal_mem_Ine"),
    # where the theorem is used
    ("xUnip", "PropA.xUnip", AV + "AdditiveValuationNorms/XUnip.lean", "theorem", "UpperTheory.V.PropA.xUnip"),
    ("dualUnip", "PropA.dualUnip", AV + "AdditiveValuationNorms/DualUnip.lean", "theorem", "UpperTheory.V.PropA.dualUnip"),
    ("shaDGen", "Tower.shaDGen", AV + "NumberFieldTowers/ShaDGen.lean", "theorem", "UpperTheory.V.Tower.shaDGen"),
]
QUOTED = ["dinfNil", "XDual", "funRepMem"]                 # statements printed in the appendix
LETTERED = [("Theorem A", "t:A")]

# the outline of the chapter: the part treated here ...
OUTLINE = [
    ("characters", "Characters and conjugation", "locally constant homomorphisms with conditions at the places; conjugation acts on them",
     ["XDual", "Dinf", "Xinf", "funRep", "conjCond", "EqHom", "Un", "funRepMem"]),
    ("nilpotence", "Local nilpotence", "a character is fixed by a congruence subgroup, and is killed by a power of g - 1",
     ["memPrinc", "powSucc", "qzTors", "princNhds", "dinfNil"]),
]
# ... and the subjects of the other members of the unit, by source file (provisional; notes to come)
ELSEWHERE = [
    ("artin", "The Artin map and class groups",
     ["ArtConj.lean", "ArtFrob.lean", "ArtSurj.lean", "ClMapBasic.lean", "ClProd.lean", "ClPullApply.lean",
      "ClSubUniv.lean", "ToGalDict.lean"]),
    ("kummer", "Kummer generators, units and Selmer groups",
     ["CardSUnit.lean", "CardSel.lean", "DvdOfIne.lean", "FinChar.lean", "RadClKer.lean", "RadClMap.lean",
      "RadClMul.lean", "RadClSurj.lean", "RadConj.lean", "RadXDual.lean"]),
    ("reflection", "Reflection", ["ReflMap.lean", "ReflRoot.lean", "ReflTw.lean"]),
    ("restriction", "Restriction to the cyclotomic kernel",
     ["ResInfConj.lean", "ResInfInj.lean", "ResInfMem.lean", "ResInfOnto.lean", "VanishCyc.lean", "ExtCocycle.lean",
      "CobOfGen.lean", "CycZConjGal.lean", "XdualExt.lean", "XdualBase.lean", "RestrMem.lean", "MinusLenLeOfCl.lean",
      "FnCycMap.lean"]),
    ("definitions", "Definitions of the other subjects", ["Mk0IdMapCongr.lean"]),
]
