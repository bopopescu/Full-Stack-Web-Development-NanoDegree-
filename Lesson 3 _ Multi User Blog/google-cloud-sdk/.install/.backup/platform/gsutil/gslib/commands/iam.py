# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Implementation of IAM policy management command for GCS."""
from __future__ import absolute_import

import itertools
import json

from apitools.base.protorpclite import protojson
from gslib.cloud_api import ArgumentException
from gslib.cloud_api import PreconditionException
from gslib.cloud_api import ServiceException
from gslib.command import Command
from gslib.command import GetFailureCount
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.help_provider import CreateHelpText
from gslib.iamhelpers import BindingStringToTuple
from gslib.iamhelpers import BindingsTuple
from gslib.iamhelpers import DeserializeBindingsTuple
from gslib.iamhelpers import IsEqualBindings
from gslib.iamhelpers import PatchBindings
from gslib.iamhelpers import SerializeBindingsTuple
from gslib.metrics import LogCommandParams
from gslib.name_expansion import NameExpansionIterator
from gslib.name_expansion import SeekAheadNameExpansionIterator
from gslib.plurality_checkable_iterator import PluralityCheckableIterator
from gslib.storage_url import StorageUrlFromString
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.util import GetCloudApiInstance
from gslib.util import NO_MAX
from gslib.util import Retry

_WHITELIST_URL = 'https://docs.google.com/a/google.com/forms/d/1OyFkWmWXY08XNHO8qHNvJxcjVXtsNmGYYxpibq7M_Xs/viewform'

_ALPHA_DISCLAIMER = """
  Note: As of 2016 May 15, Identity and Access Management (IAM) support is
  in alpha, and is not covered by any SLA or deprecation policy and may be
  subject to backward-incompatible changes. These commands are only usable
  by whitelisted projects. You may apply to be on the whitelist by visiting
  %s
""" % _WHITELIST_URL

_SET_SYNOPSIS = """
  gsutil iam set [-afRr] file url ...
"""

_GET_SYNOPSIS = """
  gsutil iam get url
"""

_CH_SYNOPSIS = """
  gsutil iam ch [-fRr] binding ...

  where each binding is of the form:

      [-d] ("user"|"serviceAccount"|"domain"|"group"):id:role[,...]
      [-d] ("allUsers"|"allAuthenticatedUsers"):role[,...]
      -d ("user"|"serviceAccount"|"domain"|"group"):id
      -d ("allUsers"|"allAuthenticatedUsers")
"""

_GET_DESCRIPTION = """
<B>GET</B>
  The "iam get" command gets the IAM policy for a bucket or object, which you
  can save and edit for use with the "iam set" command.

  For example:

    gsutil iam get gs://example > bucket_iam.txt
    gsutil iam get gs://example/important.txt > object_iam.txt
"""

_SET_DESCRIPTION = """
<B>SET</B>

  The "iam set" command sets the IAM policy for one or more buckets and / or
  objects. It overwrites the current IAM policy that exists on a bucket (or
  object) with the policy specified in the input file. The "iam set" command
  takes as input a file with an IAM policy in the format of the output
  generated by "iam get".

  The "iam ch" command can be used to edit an existing policy. It works
  correctly in the presence of concurrent updates.

  If you wish to set an IAM policy on a large number of objects, you may want
  to use the gsutil -m option for concurrent processing. The following command
  will apply iam.text to all objects in the "cats" bucket.

    gsutil -m iam set -r iam.txt gs://cats

  Note that only object-level IAM applications are parallelized; you do not
  gain any additional performance when applying an IAM policy to a large
  number of buckets with the -m flag.

<B>SET OPTIONS</B>
  The "set" sub-command has the following options

    -R, -r      Performs "iam set" recursively to all objects under the
                specified bucket.

    -a          Performs "iam set" request on all object versions.

    -f          Default gsutil error handling is fail-fast. This flag
                changes the request to fail-silent mode. This is implicitly
                set when invoking the gsutil -m option.
"""

_CH_DESCRIPTION = """
<B>CH</B>
  The "iam ch" command incrementally updates IAM policies. You may specify
  multiple access grants and removals in a single command invocation, which
  will be batched and applied as a whole to each url via an IAM patch.
  The patch will be constructed by applying each access grant or removal in the
  order in which they appear in the command line arguments. Each access change
  specifies a member and the role that will be either granted or revoked.

  The gsutil -m option may be set to handle object-level operations more
  efficiently.

<B>CH EXAMPLES</B>
  Examples for the "ch" sub-command:

  To grant a single role to a single member for some targets:

    gsutil iam ch user:john.doe@example.com:objectCreator gs://ex-bucket

  To make a bucket's objects publically readable:

    gsutil iam ch allUsers:objectViewer gs://ex-bucket

  To grant multiple bindings to a bucket:

    gsutil iam ch user:john.doe@example.com:objectCreator \\
                  domain:www.my-domain.org:objectViewer gs://ex-bucket

  To specify more than one role for a particular member:

    gsutil iam ch user:john.doe@example.com:objectCreator,objectViewer \\
                  gs://ex-bucket

  To apply a grant and simultaneously remove a binding to a bucket:

    gsutil iam ch -d group:readers@example.com:legacyBucketReader \\
                  group:viewers@example.com:objectViewer gs://ex-bucket

  To remove a user from all roles on a bucket:

    gsutil iam ch -d user:john.doe@example.com gs://ex-bucket

<B>CH OPTIONS</B>
  The "ch" sub-command has the following options

    -R, -r      Performs "iam ch" recursively to all objects under the
                specified bucket.

    -f          Default gsutil error handling is fail-fast. This flag
                changes the request to fail-silent mode. This is implicitly
                set when invoking the gsutil -m option.
"""

_SYNOPSIS = (_ALPHA_DISCLAIMER + '\n' +
             _SET_SYNOPSIS.lstrip('\n') + _GET_SYNOPSIS.lstrip('\n') +
             _CH_SYNOPSIS.lstrip('\n') + '\n\n')

_DESCRIPTION = ("""
  The iam command has three sub-commands:
""" + '\n'.join([_GET_DESCRIPTION, _SET_DESCRIPTION, _CH_DESCRIPTION]))

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

_get_help_text = CreateHelpText(
    _ALPHA_DISCLAIMER + _GET_SYNOPSIS, _GET_DESCRIPTION)
_set_help_text = CreateHelpText(
    _ALPHA_DISCLAIMER + _SET_SYNOPSIS, _SET_DESCRIPTION)
_ch_help_text = CreateHelpText(
    _ALPHA_DISCLAIMER + _CH_SYNOPSIS, _CH_DESCRIPTION)


def _PatchIamWrapper(cls, iter_result, thread_state):
  (serialized_bindings_tuples, expansion_result) = iter_result
  return cls.PatchIamHelper(
      expansion_result.expanded_storage_url,
      # Deserialize the JSON object passed from Command.Apply.
      [DeserializeBindingsTuple(t) for t in serialized_bindings_tuples],
      thread_state=thread_state)


def _SetIamWrapper(cls, iter_result, thread_state):
  (serialized_policy, expansion_result) = iter_result
  return cls.SetIamHelper(
      expansion_result.expanded_storage_url,
      # Deserialize the JSON object passed from Command.Apply.
      protojson.decode_message(apitools_messages.Policy, serialized_policy),
      thread_state=thread_state)


def _SetIamExceptionHandler(cls, e):
  cls.logger.error(str(e))


def _PatchIamExceptionHandler(cls, e):
  cls.logger.error(str(e))


class IamCommand(Command):
  """Implementation of gsutil iam command."""

  command_spec = Command.CreateCommandSpec(
      'iam',
      min_args=2,
      max_args=NO_MAX,
      supported_sub_args='afRrd:',
      file_url_ok=True,
      provider_url_ok=False,
      urls_start_arg=1,
      gs_api_support=[ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments={
          'get': [
              CommandArgument.MakeNCloudURLsArgument(1)
          ],
          'set': [
              CommandArgument.MakeNFileURLsArgument(1),
              CommandArgument.MakeZeroOrMoreCloudURLsArgument()
          ],
          'ch': [
              CommandArgument.MakeOneOrMoreBindingsArgument(),
              CommandArgument.MakeZeroOrMoreCloudURLsArgument()
          ],
      },
  )

  help_spec = Command.HelpSpec(
      help_name='iam',
      help_name_aliases=[],
      help_type='command_help',
      help_one_line_summary=('Get, set, or change'
                             ' bucket and/or object IAM permissions.'),
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={
          'get': _get_help_text, 'set': _set_help_text, 'ch': _ch_help_text,
      }
  )

  def GetIamHelper(self, storage_url, thread_state=None):
    """Gets an IAM policy for a single, resolved bucket / object URL.

    Args:
      storage_url: A CloudUrl instance with no wildcards, pointing to a
                   specific bucket or object.
      thread_state: CloudApiDelegator instance which is passed from
                    command.WorkerThread.__init__() if the global -m flag is
                    specified. Will use self.gsutil_api if thread_state is set
                    to None.

    Returns:
      Serialized Policy instance.
    """

    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)

    if storage_url.IsBucket():
      policy = gsutil_api.GetBucketIamPolicy(
          storage_url.bucket_name,
          provider=storage_url.scheme,
      )
    else:
      policy = gsutil_api.GetObjectIamPolicy(
          storage_url.bucket_name,
          storage_url.object_name,
          generation=storage_url.generation,
          provider=storage_url.scheme,
      )

    return policy

  def _GetIam(self, pattern, thread_state=None):
    """Gets IAM policy for single bucket or object."""

    matches = PluralityCheckableIterator(
        self.WildcardIterator(pattern).IterAll(bucket_listing_fields=['name'])
    )
    if matches.IsEmpty():
      raise CommandException('%s matched no URLs' % pattern)
    if matches.HasPlurality():
      raise CommandException(
          '%s matched more than one URL, which is not allowed by the %s '
          'command' % (pattern, self.command_name))

    storage_url = StorageUrlFromString(list(matches)[0].url_string)
    return self.GetIamHelper(storage_url, thread_state=thread_state)

  def _SetIamHelperInternal(self, storage_url, policy, thread_state=None):
    """Sets IAM policy for a single, resolved bucket / object URL.

    Args:
      storage_url: A CloudUrl instance with no wildcards, pointing to a
                   specific bucket or object.
      policy: A Policy object to set on the bucket / object.
      thread_state: CloudApiDelegator instance which is passed from
                    command.WorkerThread.__init__() if the -m flag is
                    specified. Will use self.gsutil_api if thread_state is set
                    to None.

    Raises:
      ServiceException passed from the API call if an HTTP error was returned.
    """

    # SetIamHelper may be called by a command.WorkerThread. In the
    # single-threaded case, WorkerThread will not pass the CloudApiDelegator
    # instance to thread_state. GetCloudInstance is called to resolve the
    # edge case.
    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)

    if storage_url.IsBucket():
      gsutil_api.SetBucketIamPolicy(
          storage_url.bucket_name, policy, provider=storage_url.scheme)
    else:
      gsutil_api.SetObjectIamPolicy(
          storage_url.bucket_name, storage_url.object_name, policy,
          generation=storage_url.generation, provider=storage_url.scheme)

  def SetIamHelper(self, storage_url, policy, thread_state=None):
    """Handles the potential exception raised by the internal set function."""
    try:
      self._SetIamHelperInternal(
          storage_url, policy, thread_state=thread_state)
    except ServiceException:
      if self.continue_on_error:
        self.everything_set_okay = False
      else:
        raise

  def PatchIamHelper(
      self, storage_url, bindings_tuples, thread_state=None):
    """Patches an IAM policy for a single, resolved bucket / object URL.

    The patch is applied by altering the policy from an IAM get request, and
    setting the new IAM with the specified etag. Because concurrent IAM set
    requests may alter the etag, we may need to retry this operation several
    times before success.

    Args:
      storage_url: A CloudUrl instance with no wildcards, pointing to a
                   specific bucket or object.
      bindings_tuples: A list of BindingsTuple instances.
      thread_state: CloudApiDelegator instance which is passed from
                    command.WorkerThread.__init__() if the -m flag is
                    specified. Will use self.gsutil_api if thread_state is set
                    to None.
    """
    try:
      self._PatchIamHelperInternal(
          storage_url, bindings_tuples, thread_state=thread_state)
    except ServiceException:
      if self.continue_on_error:
        self.everything_set_okay = False
      else:
        raise

  @Retry(PreconditionException, tries=3, timeout_secs=1.0)
  def _PatchIamHelperInternal(
      self, storage_url, bindings_tuples, thread_state=None):

    policy = self.GetIamHelper(storage_url, thread_state=thread_state)
    (etag, bindings) = (policy.etag, policy.bindings)

    # Create a backup which is untainted by any references to the original
    # bindings.
    orig_bindings = list(bindings)

    for (is_grant, diff) in bindings_tuples:
      bindings = PatchBindings(bindings, BindingsTuple(is_grant, diff))

    if IsEqualBindings(bindings, orig_bindings):
      self.logger.info('No changes made to %s', storage_url)
      return

    policy = apitools_messages.Policy(bindings=bindings, etag=etag)

    # We explicitly wish for etag mismatches to raise an error and allow this
    # function to error out, so we are bypassing the exception handling offered
    # by IamCommand.SetIamHelper in lieu of our own handling (@Retry).
    self._SetIamHelperInternal(
        storage_url, policy, thread_state=thread_state)

  def _PatchIam(self):
    self.continue_on_error = False
    self.recursion_requested = False

    patch_bindings_tuples = []

    if self.sub_opts:
      for o, a in self.sub_opts:
        if o in ['-r', '-R']:
          self.recursion_requested = True
        elif o == '-f':
          self.continue_on_error = True
        elif o == '-d':
          patch_bindings_tuples.append(BindingStringToTuple(False, a))

    patterns = []

    # N.B.: self.sub_opts stops taking in options at the first non-flagged
    # token. The rest of the tokens are sent to self.args. Thus, in order to
    # handle input of the form "-d <binding> <binding> <url>", we will have to
    # parse self.args for a mix of both bindings and CloudUrls. We are not
    # expecting to come across the -r, -f flags here.
    it = iter(self.args)
    for token in it:
      if token == '-d':
        patch_bindings_tuples.append(
            BindingStringToTuple(False, it.next()))
      else:
        try:
          patch_bindings_tuples.append(
              BindingStringToTuple(True, token)
          )
        # All following arguments are urls.
        except (ArgumentException, CommandException):
          patterns.append(token)
          for token in it:
            patterns.append(token)

    # We must have some bindings to process, else this is pointless.
    if not patch_bindings_tuples:
      raise CommandException('Must specify at least one binding.')

    self.everything_set_okay = True
    threaded_wildcards = []
    for pattern in patterns:
      surl = StorageUrlFromString(pattern)
      try:
        if surl.IsBucket():
          if self.recursion_requested:
            surl.object = '*'
            threaded_wildcards.append(surl.url_string)
          else:
            self.PatchIamHelper(surl, patch_bindings_tuples)
        else:
          threaded_wildcards.append(surl.url_string)
      except AttributeError:
        error_msg = 'Invalid Cloud URL "%s".' % surl.object_name
        if set(surl.object_name).issubset(set('-Rrf')):
          error_msg += (
              ' This resource handle looks like a flag, which must appear '
              'before all bindings. See "gsutil help iam ch" for more details.'
          )
        raise CommandException(error_msg)

    if threaded_wildcards:
      name_expansion_iterator = NameExpansionIterator(
          self.command_name, self.debug,
          self.logger, self.gsutil_api,
          threaded_wildcards, self.recursion_requested,
          all_versions=self.all_versions,
          continue_on_error=self.continue_on_error or self.parallel_operations,
          bucket_listing_fields=['name'])

      seek_ahead_iterator = SeekAheadNameExpansionIterator(
          self.command_name, self.debug, self.GetSeekAheadGsutilApi(),
          threaded_wildcards, self.recursion_requested,
          all_versions=self.all_versions)

      # N.B.: Python2.6 support means we can't use a partial function here to
      # curry the bindings tuples into the wrapper function. We instead pass
      # the bindings along by zipping them with each name_expansion_iterator
      # result. See http://bugs.python.org/issue5228.
      serialized_bindings_tuples_it = itertools.repeat(
          [SerializeBindingsTuple(t) for t in patch_bindings_tuples])
      self.Apply(
          _PatchIamWrapper,
          itertools.izip(
              serialized_bindings_tuples_it, name_expansion_iterator),
          _PatchIamExceptionHandler,
          fail_on_error=not self.continue_on_error,
          seek_ahead_iterator=seek_ahead_iterator)

      self.everything_set_okay &= not GetFailureCount() > 0

    # TODO: Add an error counter for files and objects.
    if not self.everything_set_okay:
      raise CommandException('Some IAM policies could not be patched.')

  # TODO(iam-beta): Add an optional flag to specify etag and edit the policy
  # accordingly to be passed into the helper functions.
  def _SetIam(self):
    """Set IAM policy for given wildcards on the command line."""

    self.continue_on_error = False
    self.recursion_requested = False
    self.all_versions = False
    if self.sub_opts:
      for o, unused_a in self.sub_opts:
        if o in ['-r', '-R']:
          self.recursion_requested = True
        elif o == '-f':
          self.continue_on_error = True
        elif o == '-a':
          self.all_versions = True
        else:
          self.RaiseInvalidArgumentException()

    file_url = self.args[0]
    patterns = self.args[1:]

    # Load the IAM policy file and raise error if the file is invalid JSON or
    # does not exist.
    try:
      with open(file_url, 'r') as fp:
        bindings = json.loads(fp.read())
    except (IOError, ValueError):
      raise ArgumentException('Invalid IAM policy file "%s".' % file_url)

    policy = apitools_messages.Policy(bindings=bindings)

    self.everything_set_okay = True

    # This list of wildcard strings will be handled by NameExpansionIterator.
    threaded_wildcards = []

    for pattern in patterns:
      surl = StorageUrlFromString(pattern)
      if surl.IsBucket():
        if self.recursion_requested:
          surl.object_name = '*'
          threaded_wildcards.append(surl.url_string)
        else:
          self.SetIamHelper(surl, policy)
      else:
        threaded_wildcards.append(surl.url_string)

    # N.B.: If threaded_wildcards contains a non-existent bucket
    # (e.g. ["gs://non-existent", "gs://existent"]), NameExpansionIterator
    # will raise an exception in iter.next. This halts all iteration, even
    # when -f is set. This behavior is also evident in acl set. This behavior
    # also appears for any exception that will be raised when iterating over
    # wildcard expansions (access denied if bucket cannot be listed, etc.).
    if threaded_wildcards:
      name_expansion_iterator = NameExpansionIterator(
          self.command_name, self.debug,
          self.logger, self.gsutil_api,
          threaded_wildcards, self.recursion_requested,
          all_versions=self.all_versions,
          continue_on_error=self.continue_on_error or self.parallel_operations,
          bucket_listing_fields=['name'])

      seek_ahead_iterator = SeekAheadNameExpansionIterator(
          self.command_name, self.debug, self.GetSeekAheadGsutilApi(),
          threaded_wildcards, self.recursion_requested,
          all_versions=self.all_versions)

      # We cannot curry policy along due to a Python2.6 bug; see comments in
      # IamCommand._PatchIam for more information.
      policy_it = itertools.repeat(protojson.encode_message(policy))
      self.Apply(
          _SetIamWrapper,
          itertools.izip(
              policy_it, name_expansion_iterator),
          _SetIamExceptionHandler,
          fail_on_error=not self.continue_on_error,
          seek_ahead_iterator=seek_ahead_iterator)

      self.everything_set_okay &= not GetFailureCount() > 0

    # TODO: Add an error counter for files and objects.
    if not self.everything_set_okay:
      raise CommandException('Some IAM policies could not be set.')

  def RunCommand(self):
    """Command entry point for the acl command."""
    action_subcommand = self.args.pop(0)
    self.ParseSubOpts(check_args=True)
    # Commands with both suboptions and subcommands need to reparse for
    # suboptions, so we log again.
    LogCommandParams(sub_opts=self.sub_opts)
    self.def_acl = False
    if action_subcommand == 'get':
      LogCommandParams(subcommands=[action_subcommand])
      policy = self._GetIam(self.args[0])
      bindings = [
          json.loads(protojson.encode_message(b)) for b in policy.bindings]
      print json.dumps(bindings, sort_keys=True, indent=2)
    elif action_subcommand == 'set':
      LogCommandParams(subcommands=[action_subcommand])
      self._SetIam()
    elif action_subcommand == 'ch':
      LogCommandParams(subcommands=[action_subcommand])
      self._PatchIam()
    else:
      raise CommandException(
          'Invalid subcommand "%s" for the %s command.\n'
          'See "gsutil help iam".' % (action_subcommand, self.command_name))

    return 0
