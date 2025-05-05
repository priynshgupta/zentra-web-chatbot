import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Grid,
    Chip,
    CircularProgress,
    Alert,
    Tabs,
    Tab,
    Button
} from '@mui/material';
import { Link } from 'react-router-dom';

const WebsiteList = () => {
    const [websites, setWebsites] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState(0);

    const fetchWebsites = async (type = 'all') => {
        try {
            setLoading(true);
            setError(null);

            let response;
            if (type === 'all') {
                response = await axios.get('/api/website/list');
            } else if (type.startsWith('industry:')) {
                const industry = type.split(':')[1];
                response = await axios.get(`/api/website/industry/${industry}`);
            } else if (type.startsWith('type:')) {
                const websiteType = type.split(':')[1];
                response = await axios.get(`/api/website/type/${websiteType}`);
            }

            if (response.data.success) {
                setWebsites(response.data.websites);
            }
        } catch (error) {
            setError(error.response?.data?.error || 'Failed to fetch websites');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWebsites();
    }, []);

    const handleTabChange = (event, newValue) => {
        setActiveTab(newValue);
        const type = event.target.getAttribute('data-type');
        fetchWebsites(type);
    };

    const renderWebsiteCard = (website) => (
        <Card key={website.url} sx={{ mb: 2 }}>
            <CardContent>
                <Grid container spacing={2}>
                    <Grid item xs={12}>
                        <Typography variant="h6" component="div">
                            {website.url}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                            Industry
                        </Typography>
                        <Typography variant="body2">
                            {website.categories?.primary_industry}
                        </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" color="text.secondary">
                            Website Type
                        </Typography>
                        <Typography variant="body2">
                            {website.categories?.website_type}
                        </Typography>
                    </Grid>
                    <Grid item xs={12}>
                        <Typography variant="subtitle2" color="text.secondary">
                            Status
                        </Typography>
                        <Chip
                            label={website.status}
                            color={
                                website.status === 'completed' ? 'success' :
                                website.status === 'processing' ? 'warning' :
                                website.status === 'failed' ? 'error' : 'default'
                            }
                            size="small"
                        />
                    </Grid>
                    <Grid item xs={12}>
                        <Button
                            component={Link}
                            to={`/website/${encodeURIComponent(website.url)}`}
                            variant="outlined"
                            size="small"
                        >
                            View Details
                        </Button>
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
    );

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
                Processed Websites
            </Typography>

            <Tabs
                value={activeTab}
                onChange={handleTabChange}
                sx={{ mb: 3 }}
            >
                <Tab label="All" data-type="all" />
                <Tab label="Banking" data-type="industry:banking" />
                <Tab label="Technology" data-type="industry:technology" />
                <Tab label="E-commerce" data-type="type:ecommerce" />
                <Tab label="Corporate" data-type="type:corporate" />
            </Tabs>

            {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                    <CircularProgress />
                </Box>
            ) : error ? (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            ) : websites.length === 0 ? (
                <Alert severity="info">
                    No websites have been processed yet.
                </Alert>
            ) : (
                <Grid container spacing={2}>
                    {websites.map(renderWebsiteCard)}
                </Grid>
            )}
        </Box>
    );
};

export default WebsiteList; 