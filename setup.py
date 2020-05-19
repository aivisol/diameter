from distutils.core import setup
setup(
  name = 'diameter',
  packages = ['diameter', 'diameter.node'],
  version = '0.1',
  license='BSD',
  description = 'Diameter protocol implementation for python3',
  author = 'aivisol',
  author_email = 'support@datatechlabs.com', 
  url = 'https://github.com/aivisol/diameter',
  # download_url = 'https://github.com/aivisol/diameter/v_01.tar.gz',
  keywords = ['diameter', 'aaa', 'authentication', 'authorization', 'accounting', 'dcca'],
  install_requires=[
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.7',
  ],
)