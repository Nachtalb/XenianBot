<b>Direct Commands:</b>
\n
% for group_name, command_list in direct_commands.items():
    <b>${group_name}</b>
    \n
    % for command in command_list:
        /${command['command']}
        <code>
            % for arg in command['args']:
                &lt;${arg}&gt;
            % endfor
        </code>- ${command['description']}
        \n
    % endfor
    \n
% endfor
\n
<b>Indirect Commands:</b>
\n
% for group_name, command_list in indirect_commands.items():
    <b>${group_name}</b>
    \n
    % for command in command_list:
        ${command['title']} - ${command['description']}
        \n
    % endfor
    \n
% endfor
