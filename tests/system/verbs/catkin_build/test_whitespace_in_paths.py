import os

from catkin_tools.commands.catkin import main

from ...workspace_factory import workspace_factory


def test_catkin_build_with_whitespace_in_paths():
    with workspace_factory(source_space='source packages') as wf:
        wf.add_package('foo', depends=['bar'])
        wf.add_package('bar')
        wf.build()
        print('Workspace: {0}'.format(wf.workspace))
        assert os.path.isdir(wf.workspace)
        cmd = ['build', '--no-status', '--source', wf.source_space, '--space-suffix', '_with a space']
        try:
            ret = main(cmd)
        except SystemExit as exc:
            ret = exc.code
        assert ret == 0, cmd