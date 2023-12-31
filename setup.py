from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import os
import subprocess
from urllib import request
import zipfile
import io
import shutil

class get_numpy_include(object):
    def __str__(self):
        import numpy
        return numpy.get_include()

class PrimesieveBuilder:
    def download_primesieve(self):
        url = "https://codeload.github.com/kimwalisch/primesieve/zip/refs/heads/master"
        try:
            with request.urlopen(url) as response:
                return response.read()
        except Exception as e:
            print("Error downloading primesieve:{}".format(e))
            return None
        
    def unzip_file(self, zip_content, extract_to):
        with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
            common_prefix = os.path.commonprefix(zip_ref.namelist())
            zip_ref.extractall(extract_to)

        return os.path.join(os.getcwd(), extract_to, common_prefix)

    def build_primesieve(self):
        from cmake import CMAKE_BIN_DIR

        OS = os.uname()[0]

        if OS == "Windows":
            CMAKE = os.path.join(CMAKE_BIN_DIR, "cmake.exe")
        else:
            CMAKE = os.path.join(CMAKE_BIN_DIR, "cmake")
        
        assert os.path.isfile(CMAKE)
        
        cmake_build_args = ["--parallel"]
        cmake_config_args = ["-DCMAKE_POSITION_INDEPENDENT_CODE=ON", "-DBUILD_PRIMESIEVE=OFF", "-DBUILD_SHARED_LIBS=OFF"]
        path = os.getcwd()
        primesieve_path = self.unzip_file(self.download_primesieve(), "primesieve")
        lib_path = os.path.join(primesieve_path, "lib")
        shutil.rmtree(lib_path, ignore_errors=True)
        os.makedirs(lib_path)

        config_command = [CMAKE, "-B {}".format(lib_path), "-S {}".format(primesieve_path)] + cmake_config_args
        subprocess.run(config_command)

        build_command = [CMAKE, "--build", lib_path] + cmake_build_args
        subprocess.run(build_command)

        libprimesieve_a = os.path.join(lib_path, "libprimesieve.a")
        assert os.path.isfile(libprimesieve_a)
        return {
            "libprimesieve.a": libprimesieve_a,
            "include": os.path.join(primesieve_path, "include"),
            "lib": lib_path,
        }

class Build_ext(build_ext):
    def run(self):
        builder = PrimesieveBuilder()
        dirs = builder.build_primesieve()
        libprimesieve_a = dirs["libprimesieve.a"]
        primesieve_include = dirs["include"]
        libprimesieve_path = dirs["lib"]

        self.include_dirs.append(primesieve_include)
        self.extra_objects.append(libprimesieve_a)


with open("README.md", "r") as readme_file:
    README = readme_file.read()

PandaPrimes_ext = Extension(
    name="PandaPrimes.PandaPrimes",
    sources=["PandaPrimes/src/PandaPrimes.c"],
    libraries=["stdc++",],
    include_dirs=[get_numpy_include()],
    language="c",
    extra_compile_args=["-w"],
)

setup(
    name="PandaPrimes",
    version="0.0.6",
    setup_requires=["numpy", "cmake"],
    install_requires=['setuptools', 'numpy', 'cmake'],
    packages=["PandaPrimes"],
    package_dir={'PandaPrimes': 'PandaPrimes'},
    ext_modules=[PandaPrimes_ext],
    project_urls={
        "Source": "https://github.com/PaNDa2code/PandaPrimes",
    },
    author="PaNDa2code",
    author_email="moaaz0688@gmail.com",
    description="A Python extension module for finding primes using C",
    long_description=README,
    long_description_content_type="text/markdown",
)
