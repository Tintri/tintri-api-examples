#!/usr/bin/perl

use warnings;
use strict;

use HTTP::Request::Common;
use HTTP::Cookies;
use LWP::UserAgent;

use JSON;

my $ua = LWP::UserAgent->new;

my $cookies = HTTP::Cookies->new(file => "cookies.txt", autosave => 1);

$ua->cookie_jar($cookies);

my $resp = $ua->request(POST 'https://172.16.12.48/api/v310/session/login',
                        Content_type => 'application/json',
						Content => '{"username":"admin", "typeId":"com.tintri.api.rest.vcommon.dto.rbac.RestApiCredentials",
						"password":"tintri99"}');

$resp = $ua->request(GET 'https://172.16.12.48/api/v310/virtualDisk', Content_type => 'application/json');

my $json = $resp->content();
my $info = from_json($json);

my $vms; # List of virtual disks UUID using VMname as key

foreach my $item (@{$info->{items}}) {
    push(@{$vms->{$item->{vmName}}{$item->{vmUuid}{uuid}}}, $item->{uuid}{uuid}) unless $item->{uuid}{uuid} =~ /snapshot/ || $item->{name} =~ /Swap/;
}

while (1) {
    foreach my $name (sort keys %{$vms}) {
        printf("%s:\n", $name);
        foreach my $vmuuid (sort keys %{$vms->{$name}}) {
            foreach my $uuid (sort @{$vms->{$name}{$vmuuid}}) {
                $resp = $ua->request(GET "https://172.16.12.48/api/v310/virtualDisk/$vmuuid/$uuid/statsRealtime",
                                     Content_type => 'application/json');

                my $json = $resp->content();
                my $info = from_json($json);
                foreach my $item (sort @{$info->{items}}) {
                    foreach my $stat (sort @{$item->{sortedStats}}) {
                        printf(" %s: read %f MB/s write %f MB/s IOPS: %d Latency: %f (%f / %f / %f / %f) ms\n",
					           $item->{startTime}, $stat->{throughputReadMBps}, $stat->{throughputWriteMBps}, $stat->{operationsTotalIops},
                               $stat->{latencyTotalMs}, $stat->{latencyDiskMs}, $stat->{latencyStorageMs},
							   $stat->{latencyNetworkMs}, $stat->{latencyHostMs}, );
                    }
                }
            }
        }
    }
    sleep 10;
    printf(" #################\n");
}

exit;
