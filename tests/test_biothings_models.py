"""Tests for BioThings response model coercion."""

from medical_mcps.models.biothings import MyChemDrug, MyGeneGene


def test_mygene_coerces_string_alias_to_list():
    gene = MyGeneGene(symbol="TMEM175", alias="hTMEM175")
    assert gene.alias == ["hTMEM175"]


def test_mygene_coerces_ensembl_list_to_dict():
    gene = MyGeneGene(
        symbol="DHRS1",
        ensembl=[{"gene": "ENSG00000157379", "type": "protein_coding"}],
    )
    assert gene.ensembl == {"gene": "ENSG00000157379", "type": "protein_coding"}


def test_mychem_coerces_unii_list_to_string():
    drug = MyChemDrug(name="metformin", unii=["Y15XK0XOB5"])
    assert drug.unii == "Y15XK0XOB5"
