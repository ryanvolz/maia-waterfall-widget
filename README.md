# maia_waterfall_widget

## Installation

```sh
pip install maia_waterfall_widget
```

or with [uv](https://github.com/astral-sh/uv):

```sh
uv add maia_waterfall_widget
```

## Development

We recommend using [pixi](https://pixi.prefix.dev) for development.
It will automatically manage virtual environments and dependencies for you.

To install the package from source and run the example notebook:

```sh
pixi run example
```

To use the development environment containing the editable package and all build tools:

```sh
pixi shell
```

To build Python wheel and sdist that will be placed in the `dist/` directory:
```sh
pixi run build
```

To build a conda package:
```sh
pixi publish --target-dir dist
```

To use a test environment containing the conda package:
```sh
pixi shell -e test
```

## License

Licensed under either of

 * Apache License, Version 2.0
   ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
 * MIT license
   ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option.

## Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be
dual licensed as above, without any additional terms or conditions.
