import requests

from Bio.PDB import PDBParser, PDBIO, Select
import os

import glob
from rdkit import Chem
from rdkit.Chem import Draw
from PIL import Image, ImageDraw, ImageFont
from IPython.display import display

import shutil

from IPython.display import clear_output

def download_pdb(pdb_code):
    url = f"https://files.rcsb.org/download/{pdb_code}.pdb"
    response = requests.get(url)
    if response.status_code == 200:
        with open(f"{pdb_code}.pdb", "w") as file:
            file.write(response.text)
        print(f"Файл {pdb_code}.pdb успешно скачан.")
    else:
        print(f"Ошибка при скачивании файла {pdb_code}.pdb: {response.status_code}")

class NonProteinNonWaterSelector(Select):
    def __init__(self, resname, chain, seen_ligands = ()):
        super().__init__()
        self.resname = resname
        self.chain = chain
        self.seen_ligands = seen_ligands

    def accept_atom(self, atom):
        return atom.get_parent().get_parent().id == self.chain and atom.get_parent().get_resname() == self.resname

def extract_ligands_to_smi(pdb_code):
    parser = PDBParser()
    structure = parser.get_structure('X', f'{pdb_code}.pdb')
    io = PDBIO()
    seen_ligands = set()
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.id[0] != ' ' and residue.get_resname() not in ['ALA', 'ARG', 'ASN', 'ASP', 'CYS',
                                                                          'GLU', 'GLN', 'GLY', 'HIS', 'ILE',
                                                                          'LEU', 'LYS', 'MET', 'PHE', 'PRO',
                                                                          'SER', 'THR', 'TRP', 'TYR', 'VAL', 'HOH']:
                    ligand_id = f"{residue.get_resname()}"
                    if ligand_id not in seen_ligands:
                        seen_ligands.add(ligand_id)
                        io.set_structure(structure)
                        filename = f"{ligand_id}.pdb"
                        io.save(filename, NonProteinNonWaterSelector(residue.get_resname(), chain.id, seen_ligands))
                        os.system(f"obabel {filename} -O {ligand_id}.smi")
                        os.remove(filename)
                        print(f"Сохранена молекула {ligand_id} в файл {ligand_id}.smi")

def visualize_smiles_from_files(pdb_code):
    smi_files = glob.glob(f"*.smi")

    for smi_file in smi_files:
        with open(smi_file, "r") as file:
            for line in file:
                smiles = line.strip()
                mol = Chem.MolFromSmiles(smiles)
                if mol:
                    img = Draw.MolToImage(mol, size=(300, 300))
                    draw = ImageDraw.Draw(img)
                    font = ImageFont.load_default()
                    draw.text((50, 260), f"{pdb_code}_{smi_file.split('/')[-1][:-4]}", (0, 0, 0), font=font)
                    display(img)
                else:
                    print(f"Не удалось создать молекулу из SMILES: {smiles}")

def clear_folder(folder_path):
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            shutil.rmtree(item_path)

def process_pdb(pdb_code):
    os.chdir('PDB')
    download_pdb(pdb_code)
    extract_ligands_to_smi(pdb_code)
    clear_output(wait=True)
    visualize_smiles_from_files(pdb_code)
    os.chdir(./)
    clear_folder('PDB')
    

