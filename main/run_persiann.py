#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Punto de entrada del pipeline PERSIANN."""

from modules.persiann_processor import PersiannPipelineProcessor


def main() -> None:
    PersiannPipelineProcessor().run()


if __name__ == "__main__":
    main()
