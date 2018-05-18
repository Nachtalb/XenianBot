% for group_name, command_list in direct_commands.items():
    % for command in command_list:
        ${command['command']} -
        % for arg in command['args']:
            &lt;${arg}&gt;
        % endfor
        % if command['args']:
            -
        % endif
        ${command['title']}: ${command['description']}
        <br>
    % endfor
% endfor
