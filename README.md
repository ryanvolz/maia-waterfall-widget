# maia_waterfall

maia_waterfall is a collection of packages for displaying a spectral waterfall on a web browser `<canvas>`. The waterfall display run in WebGL and is derived from Maia SDR, hence the name.

## Packages

- [maia-waterfall-js](packages/js): WebAssembly library and its Javascript wrapper
- [maia-waterfall-widget](packages/widget): Python [anywidget](https://anywidget.dev/) for use in Jupyter and Marimo notebooks

## Development

We recommend using [pixi](https://pixi.prefix.dev) for development.
It will automatically manage virtual environments and dependencies for you.

To install the package from source and run the example Jupyter notebook:

```sh
pixi run example-widget
```

To activate a test environment containing the conda packages:
```sh
pixi shell
```

To build conda packages that will be placed in the `dist/` directory:
```sh
pixi publish --target-dir dist
```

To build `maia_waterfall_widget` Python wheel and sdist that will be placed in the `dist/` directory:
```sh
pixi run build-widget-wheel
```

To publish the `maia-waterfall` Javascript package to npm:
```sh
pixi run npm-publish
```

To update dependencies and lockfiles:
```sh
pixi update
pixi run cargo-update
pixi run lock-update-widget
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
