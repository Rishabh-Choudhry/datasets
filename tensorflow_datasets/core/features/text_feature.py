# coding=utf-8
# Copyright 2018 The TensorFlow Datasets Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Text feature.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os

import tensorflow as tf

from tensorflow_datasets.core.features import feature
from tensorflow_datasets.core.features import text as text_lib


class Text(feature.FeatureConnector):
  """Feature which encodes/decodes text, possibly to integers."""

  def __init__(self, encoder=None, encoder_config=None):
    """Constructs a Text FeatureConnector.

    Args:
      encoder: `tfds.features.text.TextEncoder`, an encoder that can convert
        text to integers. If None, the text will be utf-8 byte-encoded.
      encoder_config: `tfds.features.text.TextEncoderConfig`, needed if
        restoring from a file with `load_metadata`.
    """
    if encoder and encoder_config:
      raise ValueError("If encoder is provided, encoder_config must be None.")
    if encoder:
      encoder_config = text_lib.TextEncoderConfig(
          encoder_cls=type(encoder),
          vocab_size=encoder.vocab_size)
    elif encoder_config:
      encoder = encoder_config.encoder

    self._encoder = encoder
    self._encoder_config = encoder_config

  @property
  def encoder(self):
    return self._encoder

  @encoder.setter
  def encoder(self, new_encoder):
    if self.encoder:
      raise ValueError("Cannot override encoder")
    self._encoder = new_encoder
    if not isinstance(new_encoder, self._encoder_cls):
      raise ValueError(
          "Changing type of encoder. Got %s but must be %s" %
          (type(new_encoder).__name__,
           self._encoder_cls.__name__))

  @property
  def vocab_size(self):
    return self.encoder and self.encoder.vocab_size

  def str2ints(self, str_value):
    """Conversion list[int] => decoded string."""
    if not self._encoder:
      raise ValueError(
          "Text.str2ints is not available because encoder hasn't been defined.")
    return self._encoder.encode(str_value)

  def ints2str(self, int_values):
    """Conversion string => encoded list[int]."""
    if not self._encoder:
      raise ValueError(
          "Text.ints2str is not available because encoder hasn't been defined.")
    return self._encoder.decode(int_values)

  def get_tensor_info(self):
    if self.encoder:
      return feature.TensorInfo(shape=(None,), dtype=tf.int64)
    else:
      return feature.TensorInfo(shape=(), dtype=tf.string)

  def encode_example(self, example_data):
    if self.encoder:
      return self.encoder.encode(example_data)
    else:
      return tf.compat.as_bytes(example_data)

  def decode_example(self, tfexample_data):
    return tfexample_data

  def save_metadata(self, data_dir, feature_name):
    fname_prefix = os.path.join(data_dir, "%s.text" % feature_name)
    if not self.encoder:
      return
    self.encoder.save_to_file(fname_prefix)

  def load_metadata(self, data_dir, feature_name):
    fname_prefix = os.path.join(data_dir, "%s.text" % feature_name)
    encoder_cls = self._encoder_cls
    if encoder_cls:
      self._encoder = encoder_cls.load_from_file(fname_prefix)
      return

    # Error checking: ensure there are no metadata files
    feature_files = [
        f for f in tf.gfile.ListDirectory(data_dir)
        if f.startswith(fname_prefix)
    ]
    if feature_files:
      raise ValueError(
          "Text feature files found for feature %s but encoder_cls=None. "
          "Make sure to set encoder_cls in the TextEncoderConfig. "
          "Files: %s" % (feature_name, feature_files))

  def maybe_build_from_corpus(self, corpus_generator, **kwargs):
    """Call SubwordTextEncoder.build_from_corpus is encoder_cls is such."""
    if self._encoder_cls is not text_lib.SubwordTextEncoder:
      return

    vocab_size = self._encoder_config.vocab_size
    self.encoder = text_lib.SubwordTextEncoder.build_from_corpus(
        corpus_generator=corpus_generator,
        target_vocab_size=vocab_size,
        **kwargs)

  @property
  def _encoder_cls(self):
    return self._encoder_config and self._encoder_config.encoder_cls
