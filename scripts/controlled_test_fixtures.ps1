# Generate synthetic inputs only. This script never contacts the Site or reads a profile.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('A','B')][string]$Role,
    [Parameter(Mandatory=$true)][ValidatePattern('^test:[a-z0-9][a-z0-9-]{2,39}$')][string]$Scope,
    [ValidateRange(0,99999998)][int]$ExpectedRevision=0,
    [ValidateRange(1,99999999)][int]$DatingVersion=1,
    [ValidateRange(1,99999999)][int]$FriendshipVersion=1,
    [switch]$ConfirmedAdultSyntheticTest
)
$ErrorActionPreference='Stop'
if (-not $ConfirmedAdultSyntheticTest) {
    Write-Output '{"ok":false,"code":"explicit_adult_synthetic_test_consent_required","network_calls":0}'
    exit 1
}
try {
    if (-not $env:LOCALAPPDATA) { throw 'local_storage_missing' }
    $fixtureBase=[IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'AI-SlowMatch\test-fixtures'))
    if ($fixtureBase -match '(?i)(^|[\\/])OneDrive[^\\/]*([\\/]|$)') { throw 'sync_location_rejected' }
    $fixtureParent=New-Object IO.DirectoryInfo($fixtureBase)
    while ($null -ne $fixtureParent) {
        if ($fixtureParent.Exists -and ($fixtureParent.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw 'linked_location_rejected'
        }
        $fixtureParent=$fixtureParent.Parent
    }
    $fixtureId=[guid]::NewGuid().ToString('N')
    $fixtureDirectory=Join-Path $fixtureBase $fixtureId
    [IO.Directory]::CreateDirectory($fixtureDirectory) | Out-Null
    $fixtureExpiry=[DateTime]::UtcNow.AddDays(14).ToString("yyyy-MM-ddTHH:mm:ssZ")
    $fixtureProfile=@{
        expected_revision=$ExpectedRevision;confirmed=$true;response='changes';changes=@(
            @{action='upsert';claim=@{topic='values';text="SYNTHETIC_PRIVATE_$Role`: I value honest, gradual conversation.";
                source=@{source_type='self_report';reference='Controlled synthetic test'};
                confirmation='confirmed';uncertainty='Synthetic self-report, not observed behavior.'}},
            @{action='upsert';claim=@{topic='friend_needs';text='I enjoy relaxed reading and outdoor activities.';
                source=@{source_type='self_report';reference='Controlled synthetic test'};
                confirmation='confirmed';uncertainty='A fictional preference for this test only.'}}
        )
    }
    $fixtureDating=@{
        schema_version='2.0';mode='dating';summary_id=[guid]::NewGuid().ToString('N');version=$DatingVersion;
        expires_at=$fixtureExpiry;alias="Synthetic $Role";age_band='25-34';city='Toronto';areas=@('Toronto');
        relationship_goal='long_term';accepted_goals=@('long_term');accepted_age_bands=@('25-34');
        values=@('honesty','autonomy');life_directions=@('still_exploring');
        communication_preferences=@('reflective');interests=@('reading','outdoors');preferences=@('honesty');
        visibility='participants';discoverable=$true
    }
    $fixtureFriend=@{
        schema_version='2.0';mode='friendship';summary_id=[guid]::NewGuid().ToString('N');version=$FriendshipVersion;
        expires_at=$fixtureExpiry;alias="Synthetic $Role";age_band='25-34';city='Toronto';areas=@('Toronto');
        accepted_age_bands=@('25-34');values=@('honesty','autonomy');communication_preferences=@('reflective');
        interests=@('reading','outdoors');preferences=@('honesty');visibility='participants';discoverable=$true;
        friendship_intent='activity_companions';accepted_friendship_intents=@('activity_companions');
        activity_styles=@('one_on_one','outdoors');interaction_frequency='occasional';
        accepted_frequencies=@('occasional');boundaries=@('platonic_only','privacy_respected')
    }
    $fixtureObjects=@{
        'private-profile-update.json'=$fixtureProfile;
        'dating-draft-input.json'=@{adult_confirmed=$true;expected_revision=$ExpectedRevision+1;
            destination='https://slowmatch-private-pilot.fizzydeer7.chatgpt.site';summary=$fixtureDating};
        'friendship-draft-input.json'=@{adult_confirmed=$true;expected_revision=$ExpectedRevision+1;
            destination='https://slowmatch-private-pilot.fizzydeer7.chatgpt.site';summary=$fixtureFriend};
        'test-scope.json'=@{synthetic=$true;role=$Role;expected_server_scope=$Scope;
            requires_fresh_authenticated_health=$true;does_not_authorize_upload=$true}
    }
    $fixtureUtf8=New-Object Text.UTF8Encoding($false)
    foreach ($fixtureName in $fixtureObjects.Keys) {
        [IO.File]::WriteAllText((Join-Path $fixtureDirectory $fixtureName),
            (($fixtureObjects[$fixtureName] | ConvertTo-Json -Depth 20)+[Environment]::NewLine),$fixtureUtf8)
    }
    @{ok=$true;synthetic=$true;role=$Role;expected_scope=$Scope;
        relative_localappdata_directory="AI-SlowMatch/test-fixtures/$fixtureId";
        files=@($fixtureObjects.Keys | Sort-Object);network_calls=0;model_calls=0;
        published=$false;next='Verify authenticated controlled-test scope and local ownership; preview/approve each summary separately.'
    } | ConvertTo-Json -Compress -Depth 4
} catch {
    Write-Output '{"ok":false,"code":"fixture_generation_failed","network_calls":0,"private_content_printed":false}'
    exit 1
}
