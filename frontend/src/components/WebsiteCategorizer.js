import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    Box,
    Button,
    TextField,
    Typography,
    CircularProgress,
    Card,
    CardContent,
    Grid,
    Chip,
    Alert,
    List,
    ListItem,
    ListItemText,
} from '@mui/material';

const WebsiteCategorizer = () => {
    const [url, setUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [website, setWebsite] = useState(null);
    const [polling, setPolling] = useState(false);

    const processWebsite = async () => {
        try {
            setLoading(true);
            setError(null);
            setWebsite(null);

            const response = await axios.post('/api/website/process', { url });

            if (response.data.success) {
                setPolling(true);
                pollWebsiteStatus();
            }
        } catch (error) {
            setError(error.response?.data?.error || 'Failed to process website');
            setLoading(false);
        }
    };

    const pollWebsiteStatus = async () => {
        try {
            const response = await axios.get(`/api/website/status/${encodeURIComponent(url)}`);

            if (response.data.success) {
                const websiteData = response.data.website;
                setWebsite(websiteData);

                if (websiteData.status === 'processing') {
                    // Continue polling
                    setTimeout(pollWebsiteStatus, 2000);
                } else {
                    setPolling(false);
                    setLoading(false);
                }
            }
        } catch (error) {
            setError(error.response?.data?.error || 'Failed to get website status');
            setPolling(false);
            setLoading(false);
        }
    };

    useEffect(() => {
        return () => {
            setPolling(false);
        };
    }, []);

    const renderCategories = () => {
        if (!website?.categories) return null;

        const { categories } = website;
        return (
            <Card sx={{ mt: 2 }}>
                <CardContent>
                    <Typography variant="h6" gutterBottom>
                        Website Categories
                    </Typography>
                    <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                            <Typography variant="subtitle1" color="primary">
                                Industry
                            </Typography>
                            <Typography variant="body1">
                                {categories.primary_industry}
                                ({Math.round(categories.industry_confidence * 100)}% confidence)
                            </Typography>
                        </Grid>
                        <Grid item xs={12} md={6}>
                            <Typography variant="subtitle1" color="primary">
                                Website Type
                            </Typography>
                            <Typography variant="body1">
                                {categories.website_type}
                                ({Math.round(categories.type_confidence * 100)}% confidence)
                            </Typography>
                        </Grid>
                        <Grid item xs={12}>
                            <Typography variant="subtitle1" color="primary">
                                Target Audience
                            </Typography>
                            <Typography variant="body1">
                                {categories.target_audience}
                            </Typography>
                        </Grid>
                        <Grid item xs={12}>
                            <Typography variant="subtitle1" color="primary">
                                Functionality
                            </Typography>
                            <Box sx={{ mt: 1 }}>
                                {categories.functionality.map((feature, index) => (
                                    <Chip
                                        key={index}
                                        label={feature}
                                        sx={{ mr: 1, mb: 1 }}
                                    />
                                ))}
                            </Box>
                        </Grid>
                        <Grid item xs={12}>
                            <Typography variant="subtitle1" color="primary">
                                Meta Information
                            </Typography>
                            <List dense>
                                <ListItem>
                                    <ListItemText
                                        primary="Title"
                                        secondary={categories.meta_information.title}
                                    />
                                </ListItem>
                                <ListItem>
                                    <ListItemText
                                        primary="Description"
                                        secondary={categories.meta_information.description}
                                    />
                                </ListItem>
                                <ListItem>
                                    <ListItemText
                                        primary="Keywords"
                                        secondary={categories.meta_information.keywords}
                                    />
                                </ListItem>
                            </List>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>
        );
    };

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
                Website Categorizer
            </Typography>

            <Box sx={{ mb: 3 }}>
                <TextField
                    fullWidth
                    label="Website URL"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com"
                    sx={{ mb: 2 }}
                />
                <Button
                    variant="contained"
                    onClick={processWebsite}
                    disabled={loading || !url}
                    startIcon={loading && <CircularProgress size={20} />}
                >
                    {loading ? 'Processing...' : 'Analyze Website'}
                </Button>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {website && renderCategories()}
        </Box>
    );
};

export default WebsiteCategorizer;